#!/usr/bin/env python3
"""
fable_review_roi_probe.py — Phase 1.5B: does Fable's editorial REVIEW earn
its price, or can Opus judge a draft's real problems just as well?

PIVOTED 2026-08-10 from an original "Fable rewrite vs Opus rewrite" design
after three cheap checks (see .claude/current-work.md) found that design
answered a question production had already made moot:
  1. probe_out/*.md files are FINAL pipeline output (post-review/rewrite/
     gate) -- _run_one_sample() only reads drafts_dir AFTER
     _run_production_automation_locked() returns. Reusing them as fresh
     review inputs would have been a biased test (already-polished text).
  2. _fable_polish_rewrite already passes prefer_opus=True (commit 26f5e77,
     12:19 today) -- across every real+probe sample logged since, Opus won
     the rewrite on the FIRST attempt 100% of the time (0/36 Fable
     fallback). Not currently a meaningful cost center to A/B test.
  3. Fable's REVIEW call fires on every real production run and has NEVER
     once returned publish_as_is (0/39 logged, real or probe) -- it is the
     actual recurring, load-bearing, expensive seat, and that 0/39 pattern
     is itself a hypothesis worth testing (structural over-editing bias, or
     drafts genuinely always need work -- this probe should tell us which).

DESIGN (locked, do not deviate without re-confirming — see current-work.md):
    ONE raw Opus draft, captured live (never reused from probe_out)
                    |
             /              \\
        Fable review      Opus review
     (byte-identical prompt/schema, forced model, no fallback chain)
             |                  |
        verdict+notes      verdict+notes
             |                  |
     if revise: Opus executes   if revise: Opus executes
     (same executor template,   (same executor template,
      authorship-agnostic)       authorship-agnostic)
     else: final = raw,         else: final = raw,
     unchanged                  unchanged
             |                  |
        final_from_          final_from_
        fable_review.md      opus_review.md

publish_as_is is a LEGITIMATE, first-class outcome for either branch, not a
skip condition -- the decision not to intervene is part of what's being
measured. No downstream rewrite/gate runs after the branch point; the
harness aborts the underlying pipeline run immediately after capturing the
raw draft (via a sentinel exception from the review-capture stub) so no
extra real API spend happens beyond draft generation itself.

8 cases planned: 2 raw drafts each for Siri/sauna, Zen/hiring_tool,
Maya/curb_cuts, Pixel/museum_labels (the 4 already-frozen topics/briefs --
no new topic/brief work needed).

Zero production-state mutation: reuses snapshot_test.py's _isolate_paths /
_import_orchestrator exactly like phase_probe.py. No commit, no image gen,
no persona-state writes, no real gate/rewrite calls.

Per case, persisted under automation/probe_out/fable-review-roi-ab/case-NN/:
    raw_draft.md
    review_fable.json          (verdict, notes, usage, latency, error)
    review_opus.json           (verdict, notes, usage, latency, error)
    final_from_fable_review.md (== raw_draft.md byte-for-byte if Fable said publish_as_is)
    final_from_opus_review.md  (== raw_draft.md byte-for-byte if Opus said publish_as_is)
    provenance.json            (models, prompt_hash, draft_hash, review-output
                                 hashes, tokens, latency; cost deliberately
                                 omitted -- no verified per-token pricing for
                                 the Fable alias, do not fabricate one)

USAGE:
    python3 automation/fable_review_roi_probe.py --preflight
    python3 automation/fable_review_roi_probe.py --run
    python3 automation/fable_review_roi_probe.py --summary
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

AUTOMATION_DIR = Path(__file__).parent
REPO_ROOT = AUTOMATION_DIR.parent
PROBE_OUT_DIR = AUTOMATION_DIR / "probe_out"
ROI_OUT_DIR = PROBE_OUT_DIR / "fable-review-roi-ab"
CASES_PER_TOPIC = 2

sys.path.insert(0, str(AUTOMATION_DIR))
from snapshot_test import (  # noqa: E402
    _import_orchestrator, _patch_methods, _isolate_paths,
    FIXTURE_RECENT_POSTS, FIXTURE_PERSONA_STATE, FIXTURE_FAULT_LINE,
)
from phase_probe import (  # noqa: E402
    PROBE_TOPICS, SUPPLEMENTAL_TOPICS, PROBE_REGISTER, PROBE_LENGTH,
    PROBE_ARTICLE_TYPE, PROBE_TEMPERATURE, _load_frozen_brief,
)

ROI_TOPICS = PROBE_TOPICS + SUPPLEMENTAL_TOPICS  # the 4 already-frozen topics


class _StopAfterCapture(Exception):
    """Raised inside the review-capture stub to abort the pipeline the
    instant the raw draft + persona/angle context are captured -- nothing
    downstream (real rewrite, real gate, pre-publish checks) should ever
    run for this probe. Caught in _generate_raw_draft() as the expected,
    successful exit path, not an error."""


def _sha256(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _direct_call(url, api_key, system_prompt, user_prompt, model, max_tokens, timeout,
                  reasoning_max_tokens=None):
    """Standalone HTTP call, deliberately bypassing _call_editorial_model's
    fallback chain -- every call in this probe is FORCED to one model,
    never silently substituted. Returns (text, usage_dict, latency_s,
    finish_reason, error_str_or_None)."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "stream": False,
    }
    if reasoning_max_tokens:
        body["reasoning"] = {"max_tokens": reasoning_max_tokens}
    payload = json.dumps(body).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except Exception as e:
        return None, {}, time.time() - t0, None, str(e)
    latency = time.time() - t0
    choices = data.get("choices") or []
    if not choices or not choices[0].get("message"):
        return None, data.get("usage", {}), latency, None, f"Unexpected response: {list(data.keys())}"
    finish_reason = choices[0].get("finish_reason") or data.get("native_finish_reason")
    raw_text = choices[0]["message"].get("content") or ""
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    return text, data.get("usage", {}), latency, finish_reason, None


def _review_prompts(article_body, agent_name, agent_perspective, brief_angle, register):
    """Byte-identical to _fable_editorial_review's own template in
    automation/orchestrator/llm.py — copied, not reinvented, so the A/B
    isolates the review MODEL, not the prompt wording. Used for BOTH the
    Fable-forced and Opus-forced review calls."""
    system = (
        "You are the editorial director of Crip Minds. "
        "You have just read a draft article by one of the publication's AI personas. "
        "Give 2-3 specific, actionable revision notes — or confirm it is ready. "
        "Rules you enforce: no headers, no bullet lists, first-person throughout, "
        "concrete scene before analysis, no CTA endings, disability as lens not topic.\n\n"
        "CHECKS THAT PRODUCE REVISION NOTES:\n"
        "(1) OPENING — there is no house opening and you must not enforce one. A plain expository "
        "claim, a cold scene, a bare dated fact, a rare question, and a plain statement of what the "
        "writer set out to find out are all valid; a flat claim that commits is often stronger than a "
        "scene, because the piece then has to earn it. Do NOT ask for a scene as a default. Flag only "
        "real failures: throat-clearing, context-setting, 'X has long been a problem', or a definition "
        "or framework named before anything concrete has happened. Separately: if this opening is the "
        "same shape as recent pieces — especially a body placed in a named room in the present tense — "
        "say so and ask for a different shape. That repetition is the single most visible tell across "
        "a run of articles and is invisible from inside any one of them.\n"
        "(2) COMPLICATION STANDING — is there at least one example that resists the argument and is "
        "STILL UNRESOLVED at the end? A complication introduced and then explained away does not "
        "count — that is the argument wearing a mask. Note that this is something to value when it "
        "is there, not a quota: do not ask the writer to bolt one on if the piece has no natural "
        "friction, and never ask for one that the argument would obviously defeat.\n"
        "(3) DISCOVERY — is there a moment, before the midpoint and in the past tense, where the "
        "writer was wrong, stuck, or corrected by something they encountered? An essay that knows "
        "its whole argument from the first sentence and only appends doubt at the end reads as a "
        "performance of a conclusion rather than a record of curiosity. Doubt in the final "
        "paragraph does not satisfy this.\n"
        "(4) A REAL QUOTED VOICE — does at least one other person speak inside actual quotation "
        "marks, in the past tense, saying something the narrator did not script? Conditional-mood "
        "positions ('she would say', 'he would reject this'), summarised stances, and ventriloquised "
        "objections do not count. If every quoted line serves the thesis, the writer wrote the quotes. "
        "Flag this — a piece with no other human voice in it is a monologue in a sealed room.\n"
        "(5) APHORISM DENSITY — count the short, balanced, quotable verdict-sentences (the epigram "
        "shape: 'The drop is the argument. The gender was the alibi.' / 'The frame always arrives "
        "last.'). One per piece is the cap, and a single-sentence 'arrival' paragraph counts against that "
        "same budget — one verdict-sentence total, whether it stands as its own paragraph or sits "
        "inside one. If there are two or more, name the specific ones to cut "
        "or flatten into plain prose and keep only the strongest. Three crescendos in 800 words means "
        "none of them land. Also flag it if the narrator has topped a source's line — if a person in "
        "the piece said the sharpest thing, theirs should stay the sharpest thing.\n"
        "(6) MANAGING THE READER — flag any sentence that tells the reader a connection was made "
        "rather than letting the juxtaposition do it: 'run those two facts next to each other and "
        "something clicks', 'and there it is', 'this reveals', 'that is the point', 'the two are the "
        "same thing'. Quote the sentence and say to cut it. If the connection is real the facts click "
        "on their own; if it needs the narrator's help it is not real yet. Same for any sentence whose "
        "only job is explaining the meaning of the sentence before it.\n"
        "(7) SIGNPOSTED MOVES — flag any sentence that announces the technique being performed: "
        "'here is the case I cannot fold in', 'now the person who blows this argument apart', 'here is "
        "where my own argument turns on me', 'I want to be careful here, because there is a lazy "
        "version of this argument'. The complication stays; the announcement of it goes. When a turn "
        "is announced the reader stops experiencing an argument turning and starts watching a "
        "requirement being satisfied. Quote the signpost and say to delete it, leaving the material "
        "underneath intact.\n"
        "(8) ENDING — there is no house ending shape and you must not enforce one. A hard resolution "
        "the writer commits to, a live question, a last line given to a quoted source, a plain "
        "concrete fact, a coda folding back to the opening: all valid. Judge only whether this ending "
        "is the one this piece earned. Do NOT ask for irresolution as a default — mandated "
        "irresolution reads as performed humility and forecloses the confident, warm landing that is "
        "the model's most characteristic effect. Still reject: calls to action, summaries, thesis "
        "restatements, title echoes.\n"
        "(9) WHOLENESS — every other check here tests one local thing (an opening, a quote, an "
        "aphorism count). This one asks whether the piece hangs together as ONE essay, not a "
        "sequence of individually-passable paragraphs. Four questions: (a) THROUGHLINE — could you "
        "state, in one sentence, the single thing this piece is actually about? If you need two "
        "unrelated sentences, the piece is arguing two things and one has to go. (b) SETUP AND "
        "PAYOFF — does the ending complete or reframe something the opening actually established "
        "(a person, an object, a question, a scene) — not just share a theme with it, but pay it off? "
        "If the ending could be swapped onto a different essay by the same persona with no loss, it "
        "isn't earning its place in THIS one. (c) ABANDONED THREADS — is there a person, fact, or "
        "question introduced with apparent weight that then never gets resolved or returned to? Name "
        "it specifically. (d) TONAL DRIFT — does the piece's register hold steady start to finish, or "
        "does it start as one kind of piece (wry, clinical, dry) and drift into a different register "
        "by the end without the shift being earned by the material? Flag only real drift, not natural "
        "escalation. This check can fail even when every other check passes — a piece can be locally "
        "clean and still not read as one deliberate whole.\n\n"
        "CRAFT MOVES TO NOTICE AND PRAISE WHEN THEY ARE ALREADY THERE — never to require, never to "
        "request, never to count. If one of these emerged from the material, say so in a note so it "
        "is protected in revision; if none are present, that is not a defect and generates no note: "
        "COMPARATIVE CASE (two parallel stories run side by side, the contrast carrying the argument "
        "with no commentary); CONCESSION-BEFORE-KILL (the strongest version of the opposing view "
        "given first, then one short sentence flipping it); REDEFINITION (not 'you are wrong about X' "
        "but 'X is not the problem, Y is'); READER'S INTERNAL DIALOGUE (the reader's own objection "
        "voiced before they can raise it, then answered in a sentence); INSIDER CONFESSION (someone "
        "who benefits from the system admitting it is broken — worth more than any statistic); "
        "CODA (the opening scene returned to, later or elsewhere, without stating what changed); "
        "COMPLICATING EXAMPLE (a case from inside the argument's own value system that it cannot "
        "absorb); TRANSLATED ABSTRACTION (a figure, a mechanism, or an institutional term converted "
        "into one concrete thing the reader has already been inside — a household object, a room, a "
        "bodily state, a piece of manual work — either as one flat sentence with no follow-through, "
        "or as a story told first and mapped in a single sentence at the end, such that cutting it "
        "would cost the reader understanding rather than colour). These were reverse-engineered from a finished body of work — they are the residue "
        "of a process, not the process. Requiring them is what produced technique-shaped drafts with "
        "no reporting inside them, which is why they now live here and not in the writer's brief."
    )
    user = (
        f"Persona: {agent_name} ({agent_perspective[:80]})\n"
        f"Question briefed: {brief_angle}\nStarting register: {register} (the piece is allowed to shift out of it)\n\n"
        f"DRAFT:\n{article_body[:12000]}\n\n"
        "Reply with JSON only:\n"
        '{"verdict":"publish_as_is" or "revise","notes":["note 1","note 2"]}\n'
        "Notes must name the specific paragraph or quote the specific sentence. Max 3 — "
        "if several checks fail, pick the three that most change the piece. "
        "If publish_as_is, notes may be empty."
    )
    return system, user


def _parse_review_json(raw):
    if raw is None:
        return "publish_as_is", []
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
        result = json.loads(cleaned)
        return result.get("verdict", "publish_as_is"), result.get("notes", [])[:3]
    except Exception:
        return "publish_as_is", []


def _execution_prompts(article_body, editorial_notes, agent_name):
    """Byte-identical to _opus_targeted_revision's own template — chosen
    deliberately because it's authorship-agnostic ("apply only the listed
    editorial notes", no claim about who wrote them), unlike
    _fable_polish_rewrite's "you already read this draft and wrote the
    notes below" framing, which only makes sense when reviewer==executor.
    Both branches use THIS SAME template so the execution step is
    byte-identical regardless of whether Fable or Opus authored the notes
    — only the review seat is the variable under test."""
    notes_text = "\n".join(f"- {n}" for n in editorial_notes)
    system = (
        "You are revising a draft for Crip Minds. Apply only the listed editorial notes. "
        "Do not rewrite anything not flagged. Preserve the author's voice, all facts and names, "
        "the structure, and the approximate length. "
        "No headers, no lists, no CTA endings."
    )
    user = (
        f"Persona: {agent_name}\n\nEDITORIAL NOTES:\n{notes_text}\n\n"
        f"ARTICLE:\n{article_body}\n\n"
        "Return the revised article body only — no preamble, no commentary."
    )
    return system, user


def _preflight_check():
    for t in ROI_TOPICS:
        try:
            _load_frozen_brief(t["key"])
            print(f"  {t['key']}: frozen brief OK, persona={t['persona']}")
        except Exception as e:
            print(f"  {t['key']}: {e}", file=sys.stderr)
            return False
    print(f"{len(ROI_TOPICS)} topics x {CASES_PER_TOPIC} cases = "
          f"{len(ROI_TOPICS) * CASES_PER_TOPIC} planned cases.")
    print("OK — ready to generate fresh raw drafts. Run --run to spend real API calls.")
    return True


def _generate_raw_draft(po, topic, sample_idx):
    """Runs the REAL pipeline once (same frozen-input/stubbed-side-effect
    discipline as phase_probe.py's _run_one_sample) up to and including the
    first real Opus draft, but aborts via _StopAfterCapture the INSTANT
    _fable_editorial_review is entered -- before any real review, rewrite,
    or gate call can happen. Returns
    (raw_draft, agent_name, agent_perspective, brief_angle, error_or_None)."""
    frozen_brief = _load_frozen_brief(topic["key"])
    captured = {}

    _orig_call = po.LLMMixin.__dict__["_call_openai_compat_api"]

    def temperature_pinned_call(self, url, api_key, system_prompt, user_prompt, model,
                                 max_tokens=3500, timeout=120, no_think=False,
                                 return_model=False, reasoning_max_tokens=None,
                                 check_truncation=False, temperature=None, _orig=_orig_call):
        """Pins temperature=PROBE_TEMPERATURE (0.9) for the draft-generation
        call, matching every other probe in this project -- without this,
        the raw draft would generate at the provider default (1.0),
        inconsistent with the rest of this session's corpus."""
        return _orig(
            self, url, api_key, system_prompt, user_prompt, model,
            max_tokens=max_tokens, timeout=timeout, no_think=no_think,
            return_model=return_model, reasoning_max_tokens=reasoning_max_tokens,
            check_truncation=check_truncation, temperature=PROBE_TEMPERATURE,
        )

    def capturing_review(self, article_body, agent_name, brief_angle, register):
        captured["raw_draft"] = article_body
        captured["agent_name"] = agent_name
        captured["agent_perspective"] = self.agents.get(agent_name, {}).get("perspective", "")
        captured["brief_angle"] = brief_angle
        captured["register"] = register
        raise _StopAfterCapture()

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        po_orch = po.ProductionOrchestrator()
        _isolate_paths(po_orch, tmpdir)
        po_orch.posts_dir.mkdir(parents=True, exist_ok=True)
        po_orch.drafts_dir.mkdir(parents=True, exist_ok=True)
        po_orch.assets_dir.mkdir(parents=True, exist_ok=True)
        (po_orch.repo_root / "_reviews").mkdir(exist_ok=True)
        for filename, title, body_line in FIXTURE_RECENT_POSTS:
            (po_orch.posts_dir / filename).write_text(
                f"---\ntitle: {title}\n---\n\n{body_line}\n", encoding="utf-8"
            )
        po_orch.override_agent = topic["persona"]
        po_orch.force_run = True
        ns = dict(topic["news_seed"])
        src_text = topic["source_text"]

        restore = _patch_methods(
            po.ProductionOrchestrator,
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
            _save_persona_state=lambda self, agent_name, state: None,
            _record_cited_theorists=lambda self, *a, **k: None,
            _record_beat=lambda self, *a, **k: None,
            _persist_article_plan=lambda self, *a, **k: None,
            generate_images=lambda self, *a, **k: ([], []),
            validate_article=lambda self, *a, **k: (None, True),
            commit_to_git=lambda self, *a, **k: False,
            _fable_editorial_review=capturing_review,
            _call_openai_compat_api=temperature_pinned_call,
        )
        import os as _os
        _saved_env = {k: _os.environ.pop(k, None) for k in ("REEF_BOT_TOKEN", "REEF_CHAT_ID")}
        error = None
        try:
            po_orch._run_production_automation_locked()
            error = "pipeline completed without ever reaching _fable_editorial_review (draft generation likely failed)"
        except _StopAfterCapture:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        finally:
            restore()
            for k, v in _saved_env.items():
                if v is not None:
                    _os.environ[k] = v

    if "raw_draft" not in captured:
        return None, None, None, None, error or "unknown failure before review stub reached"
    return (captured["raw_draft"], captured["agent_name"], captured["agent_perspective"],
            captured["brief_angle"], None)


def _run_one_branch(case_dir, label, raw_draft, agent_name, verdict, notes,
                     cliproxy_url, cliproxy_key):
    """label: 'fable_review' or 'opus_review'. Writing review_<label> is
    done by the caller; this only handles the execution half + final
    output, honoring publish_as_is as a legitimate no-op."""
    if verdict == "revise" and notes:
        sys_e, user_e = _execution_prompts(raw_draft, notes, agent_name)
        final_text, usage, lat, finish, err = _direct_call(
            cliproxy_url, cliproxy_key, sys_e, user_e,
            model="openrouter/claude-opus-4.8", max_tokens=5000, timeout=180,
        )
        final_text = final_text or raw_draft
    else:
        final_text, usage, lat, finish, err = raw_draft, {}, 0.0, "publish_as_is_no_op", None
    (case_dir / f"final_from_{label}.md").write_text(final_text, encoding="utf-8")
    return {"executed": verdict == "revise" and bool(notes), "usage": usage,
            "latency_s": round(lat, 2), "finish_reason": finish, "error": err,
            "output_hash": _sha256(final_text)}


def run():
    po = _import_orchestrator()
    from orchestrator.config import CLIPROXY_URL, CLIPROXY_KEY

    ROI_OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_hash = None  # filled in per-case since it includes the draft
    cases = []

    for topic in ROI_TOPICS:
        for sample_idx in range(CASES_PER_TOPIC):
            case_id = f"case-{len(cases):02d}"
            print(f"[{case_id}] {topic['key']}-{sample_idx} ({topic['persona']}): "
                  f"generating raw draft...", flush=True)
            raw_draft, agent_name, agent_perspective, brief_angle, gen_err = \
                _generate_raw_draft(po, topic, sample_idx)
            if gen_err:
                print(f"  SKIP (generation failed): {gen_err}")
                continue

            sys_r, user_r = _review_prompts(raw_draft, agent_name, agent_perspective, brief_angle, "wry")
            review_prompt_hash = _sha256(sys_r + "\n---\n" + user_r)

            print("  Fable review (forced)...", end=" ", flush=True)
            fable_raw, fable_usage, fable_lat, fable_finish, fable_err = _direct_call(
                CLIPROXY_URL, CLIPROXY_KEY, sys_r, user_r,
                model="openrouter/claude-fable-5", max_tokens=1600, timeout=90,
                reasoning_max_tokens=1024,
            )
            f_verdict, f_notes = _parse_review_json(fable_raw)
            print(f"{f_verdict} ({len(f_notes)} notes), {fable_lat:.1f}s, err={fable_err}")

            print("  Opus review (forced)...", end=" ", flush=True)
            opus_raw, opus_usage, opus_lat, opus_finish, opus_err = _direct_call(
                CLIPROXY_URL, CLIPROXY_KEY, sys_r, user_r,
                model="openrouter/claude-opus-4.8", max_tokens=1200, timeout=60,
            )
            o_verdict, o_notes = _parse_review_json(opus_raw)
            print(f"{o_verdict} ({len(o_notes)} notes), {opus_lat:.1f}s, err={opus_err}")

            case_dir = ROI_OUT_DIR / case_id
            case_dir.mkdir(parents=True, exist_ok=True)
            (case_dir / "raw_draft.md").write_text(raw_draft, encoding="utf-8")
            (case_dir / "review_fable.json").write_text(json.dumps({
                "persona": agent_name, "topic": topic["key"], "brief_angle": brief_angle,
                "verdict": f_verdict, "notes": f_notes, "raw_response": fable_raw,
            }, indent=2), encoding="utf-8")
            (case_dir / "review_opus.json").write_text(json.dumps({
                "persona": agent_name, "topic": topic["key"], "brief_angle": brief_angle,
                "verdict": o_verdict, "notes": o_notes, "raw_response": opus_raw,
            }, indent=2), encoding="utf-8")

            print(f"  -> executing Fable's review outcome...", end=" ", flush=True)
            fable_exec = _run_one_branch(case_dir, "fable_review", raw_draft, agent_name,
                                          f_verdict, f_notes, CLIPROXY_URL, CLIPROXY_KEY)
            print(f"executed={fable_exec['executed']}")

            print(f"  -> executing Opus's review outcome...", end=" ", flush=True)
            opus_exec = _run_one_branch(case_dir, "opus_review", raw_draft, agent_name,
                                         o_verdict, o_notes, CLIPROXY_URL, CLIPROXY_KEY)
            print(f"executed={opus_exec['executed']}")

            (case_dir / "provenance.json").write_text(json.dumps({
                "topic": topic["key"], "persona": agent_name, "sample_idx": sample_idx,
                "brief_angle": brief_angle,
                "review_prompt_hash": review_prompt_hash,
                "draft_hash": _sha256(raw_draft),
                "fable_review": {
                    "model": "openrouter/claude-fable-5", "verdict": f_verdict, "notes": f_notes,
                    "usage": fable_usage, "latency_s": round(fable_lat, 2),
                    "finish_reason": fable_finish, "error": fable_err,
                    "response_hash": _sha256(fable_raw),
                },
                "opus_review": {
                    "model": "openrouter/claude-opus-4.8", "verdict": o_verdict, "notes": o_notes,
                    "usage": opus_usage, "latency_s": round(opus_lat, 2),
                    "finish_reason": opus_finish, "error": opus_err,
                    "response_hash": _sha256(opus_raw),
                },
                "execute_fable_review_outcome": fable_exec,
                "execute_opus_review_outcome": opus_exec,
                "cost_usd": None,  # deliberately not estimated -- no verified per-token
                                    # pricing for the Fable alias; do not fabricate one.
            }, indent=2), encoding="utf-8")
            cases.append(case_id)

    print(f"\n{len(cases)}/{len(ROI_TOPICS) * CASES_PER_TOPIC} cases collected -> {ROI_OUT_DIR}/")
    fable_revise = sum(1 for c in cases if json.loads((ROI_OUT_DIR / c / "provenance.json").read_text())["fable_review"]["verdict"] == "revise")
    opus_revise = sum(1 for c in cases if json.loads((ROI_OUT_DIR / c / "provenance.json").read_text())["opus_review"]["verdict"] == "revise")
    print(f"Fable: revise {fable_revise}/{len(cases)}, publish_as_is {len(cases)-fable_revise}/{len(cases)}")
    print(f"Opus:  revise {opus_revise}/{len(cases)}, publish_as_is {len(cases)-opus_revise}/{len(cases)}")
    return 0


def summary():
    if not ROI_OUT_DIR.exists():
        print("No fable-review-roi-ab output yet -- run --run first.", file=sys.stderr)
        return 1
    for case_dir in sorted(ROI_OUT_DIR.glob("case-*")):
        p = json.loads((case_dir / "provenance.json").read_text())
        print(f"{case_dir.name}: {p['persona']}/{p['topic']}  "
              f"fable={p['fable_review']['verdict']}({len(p['fable_review']['notes'])}n)  "
              f"opus={p['opus_review']['verdict']}({len(p['opus_review']['notes'])}n)")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.preflight:
        sys.exit(0 if _preflight_check() else 1)
    elif args.run:
        sys.exit(run())
    elif args.summary:
        sys.exit(summary())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
