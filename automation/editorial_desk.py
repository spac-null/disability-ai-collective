"""The editorial desk's reading of a retained run. No network, no model, no writes.

WHAT THIS IS FOR. Between 10 September and today, 235 production runs produced 13
ACCEPTs, the last of them on 4 September, and the last article to reach readers went out
on 3 September. In the same period roughly twenty finished articles of 400-1,100 words
were written, held at a gate, retained on disk, and never read by a person. This module
exists so that stops.

THE ONE INVARIANT, AND THE REASON IT IS ABSOLUTE:

    IF a coherent retained article exists, it reaches the owner's desk.

Status decides what may be DONE with an article. It never decides whether the article
may be SEEN. The pipeline already demonstrated why: a run can die at SAFETY carrying two
findings at once -- a first-person passage with no cited basis, which is a real factual
problem, and `MACHINE_LANGUAGE: provenance frames ['this reading']`, which is a phrasing
tic -- and because materiality.py recognises neither category it fails closed on both
and the day ends. A desk that consulted its own classifier before delivering would
rebuild exactly that gate one layer higher, where it would be even harder to see.

SO THIS MODULE FORMS NO FACTUAL OPINION OF ITS OWN. It answers two questions:

  * is there an article here?            -- a byte question, answered from the file
  * would the existing publisher run?    -- asked of the existing publisher, verbatim

The second is delegated to publish_retained_fast_lane.resume(publish=False), which is
read-only and offline, and whose refusal text is passed through unedited. The desk never
re-derives eligibility, never softens a blocker, and never claims to have decided
materiality. Where an authoritative artifact already made a materiality judgement, the
desk quotes it; where none did, the desk says a gate held and names the stage.
"""
from __future__ import annotations

import json
import os
import pathlib

EVIDENCE_ROOT = pathlib.Path(os.environ.get("NEW_ENGINE_EVIDENCE_ROOT",
                                            "/srv/data/cripminds-new-engine-v1"))

# Delivery states. Two of them, because there are only two honest answers to "is there
# something for a person to read".
REVIEWABLE_DRAFT = "REVIEWABLE_DRAFT"
UPSTREAM_FAILURE = "UPSTREAM_FAILURE"

# Action states. Reported, never computed here -- see publish_state().
PUBLISH_ELIGIBLE = "PUBLISH_ELIGIBLE"
PUBLISH_BLOCKED = "PUBLISH_BLOCKED"

# The floor that separates "an article" from "a stub a stage emitted before it gave up".
# Deliberately far below any real article (the shortest genuine one in the last month was
# 408 words) and deliberately NOT a quality judgement: a run that falls under it is still
# reported, with its word count named, so nothing disappears quietly.
MIN_ARTICLE_WORDS = 120

# Read in this order. ARTICLE_FINAL.md is the surface the pipeline itself treats as the
# finished article; article.md is the same bytes on most runs and the only file on some
# older ones.
ARTICLE_FILES = ("ARTICLE_FINAL.md", "article.md")

# ── the reader's vocabulary ─────────────────────────────────────────────────────────
#
# NAVIGATION IS NOT FEEDBACK. Moving through an article and reacting to it are different
# acts, and a button that does both records neither cleanly. BACK and NEXT carry the
# reader; everything below carries a judgement.
NAVIGATION = ("BACK", "NEXT")

# Reader reactions, and the machine's reading of each. LEVEL 2 -- an interpretation of an
# unambiguous button the owner chose on purpose, recomputable later, and carrying no
# authority over anything. The owner's own words are never passed through this.
#
# TOO_FAST WAS RETIRED AS A BUTTON on 2026-09-27, kept here only so historical events
# stay readable. It was the nearest thing the desk offered to "too dense", and it was
# the wrong instrument: it records tempo, and the owner was reporting information
# density and report register. Three real readings were filed under it that meant
# something else. Tempo now lives where it belongs, as TOO_MUCH_AT_ONCE under density.
BUTTON_SIGNALS = {
    "TOO_DENSE": "INFORMATION_DENSITY_TOO_HIGH",
    "SOUNDS_LIKE_REPORT": "REPORT_REGISTER",
    "WHY_NOW": "READER_PURPOSE_LOST",
    "STRONG": "STRONG_PASSAGE",
    "READER_LOST": "READER_DISENGAGED",
    "WANT_MORE": "WANTS_MORE_ON_CONSEQUENCE",
    # historical, no longer offered
    "CONTINUE": "READ_THROUGH_NO_OBJECTION",
    "TOO_FAST": "IDEA_VELOCITY_TOO_HIGH",
}

# A second, OPTIONAL press that says which kind. The primary press is recorded the
# moment it happens, so skipping the detail loses nothing -- the detail refines a
# reaction that already exists, and never replaces it.
DETAIL_OPTIONS = {
    "TOO_DENSE": [("Too many names", "TOO_MANY_NAMES"),
                  ("Too many numbers", "TOO_MANY_NUMBERS"),
                  ("Too much at once", "TOO_MUCH_AT_ONCE"),
                  ("Too much jargon", "TOO_MUCH_JARGON")],
    "SOUNDS_LIKE_REPORT": [("Source summary", "SOURCE_SUMMARY"),
                           ("Institutional language", "INSTITUTIONAL_LANGUAGE"),
                           ("List of facts", "LIST_OF_FACTS"),
                           ("No story", "NO_STORY")],
}

DETAIL_SIGNALS = {
    "TOO_MANY_NAMES": "INSTITUTIONAL_LOAD_TOO_HIGH",
    "TOO_MANY_NUMBERS": "NUMERIC_LOAD_TOO_HIGH",
    "TOO_MUCH_AT_ONCE": "IDEA_VELOCITY_TOO_HIGH",
    "TOO_MUCH_JARGON": "UNGLOSSED_TERMINOLOGY",
    "SOURCE_SUMMARY": "SOURCE_SUMMARY_REGISTER",
    "INSTITUTIONAL_LANGUAGE": "INSTITUTIONAL_REGISTER",
    "LIST_OF_FACTS": "CATALOGUE_NOT_NARRATIVE",
    "NO_STORY": "NO_CARRYING_STORY",
}

# What each button asks the rewriter to do. Bounded, and every line is a constraint on
# arrangement rather than on content -- see the prohibition at the end of edit_brief().
BUTTON_INSTRUCTIONS = {
    "TOO_DENSE": "thin this out: fewer things per sentence and per paragraph, and room "
                 "around whatever survives",
    "SOUNDS_LIKE_REPORT": "stop summarising the evidence here and tell it: a person or "
                          "a concrete thing carries the paragraph, not a list of what "
                          "was found",
    "WHY_NOW": "make clear why the reader is being told this, here, before telling it",
    "READER_LOST": "this is where the reader left. Rebuild the thread into this passage "
                   "or cut what broke it",
    # NEVER "give this more room". That sentence, with no unused material supplied,
    # is an instruction to invent, and on 2026-09-27 it produced exactly that: "night
    # after night", "No door opening at two in the morning. No torch." -- all landing
    # in the paragraphs where WANT_MORE had been pressed. Expansion must name its
    # permitted sources or forbid itself.
    "WANT_MORE": ("the reader wanted to stay here. You may satisfy that ONLY by "
                  "slowing and re-paragraphing what is already here, by moving "
                  "licensed material to this point from elsewhere in the article, or "
                  "by using a licensed fact from the evidence supplied below that the "
                  "article has not yet used. If none of those is available, leave the "
                  "passage as it is -- do not expand it"),
    "STRONG": "preserve this passage. Do not rewrite it, do not compress it, do not "
              "move it later",
    "TOO_FAST": "slow the idea velocity here: let one idea land before the next arrives",
    "CONTINUE": "",
}

DETAIL_INSTRUCTIONS = {
    "TOO_MANY_NAMES": "cut or shorten the named organisations here; name one only where "
                      "the reader cannot follow the story without it",
    "TOO_MANY_NUMBERS": "keep the one figure that changes the reader's understanding and "
                        "cut the rest",
    "TOO_MUCH_AT_ONCE": "one idea at a time; let each land before the next arrives",
    "TOO_MUCH_JARGON": "say it in ordinary words, or gloss the term in the sentence that "
                       "first uses it",
    "SOURCE_SUMMARY": ("this reads as a summary of what the sources said. Write what "
                       "happened instead, using only what the evidence already "
                       "establishes"),
    "INSTITUTIONAL_LANGUAGE": "the institution is the grammatical subject here; put the "
                              "person or the thing back in that position",
    "LIST_OF_FACTS": "this is a catalogue; select, and let the unselected material go",
    "NO_STORY": ("nothing is carrying the reader through this passage. Find a concrete "
                 "thing ALREADY PRESENT in the article or in the supplied evidence to "
                 "carry it, or cut the passage. Do not invent one"),
}


def _load(run_dir: pathlib.Path, name: str) -> dict:
    """A missing or malformed artifact is a fact to report, never an exception. Same
    rule daily_run_report.py follows, and for the same reason: a broken reader must
    never look like a broken pipeline."""
    try:
        return json.loads((run_dir / name).read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── is there an article ─────────────────────────────────────────────────────────────

def artifact(run_dir, name: str) -> dict:
    """One retained artifact, read. Missing or malformed reads as {}."""
    return _load(pathlib.Path(run_dir), name)


def title_of(run_dir, text: str = "") -> str:
    """The article's headline, from the most authoritative place that has one.

    The package first, because that is the stage whose whole job is the reader who has
    never heard of this subject; then the article's own opening heading. Callers that
    have a recorded card title should prefer it -- it is what the owner was actually
    shown -- and fall back here. Before this existed the fallback was the run id, so
    the five cards delivered before card titles were recorded showed up in the inbox
    as `production-20260923T070239Z-1b5de95d`.
    """
    pkg = artifact(run_dir, "EDITORIAL_PACKAGE.json")
    t = str(pkg.get("title") or "").strip()
    if t:
        return t
    if not text:
        text, _ = article_text(pathlib.Path(run_dir))
    for line in (text or "").splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:90]
    return ""


def article_text(run_dir: pathlib.Path) -> tuple:
    """(text, filename) for the finished article, or ("", "") if none was produced."""
    for name in ARTICLE_FILES:
        p = run_dir / name
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if text.strip():
            return text.strip("\n"), name
    return "", ""


# ── what the gates said, quoted rather than re-judged ───────────────────────────────

def gate_summary(run_dir: pathlib.Path) -> dict:
    """The run's own verdicts, copied. Nothing here is recomputed or re-weighed.

    `blocking` carries the Safety findings verbatim because that is the material the
    owner needs in order to tell a real unsupported claim from a phrasing tic -- the
    distinction the pipeline currently cannot make and a person can make instantly.
    """
    comp = _load(run_dir, "COMPOSITION_RESULT.json")
    manifest = _load(run_dir, "MANIFEST.json")
    safety = _load(run_dir, "SAFETY_AUDIT.json")
    decision = _load(run_dir, "PUBLICATION_DECISION.json")
    return {
        "decision": manifest.get("decision") or comp.get("status") or "",
        "failure_stage": comp.get("failure_stage") or "",
        "failure_reason": (comp.get("failure_reason") or "")[:600],
        "reason_code": comp.get("reason_code") or "",
        "stages": comp.get("stages") or {},
        "safety_blocking": list(safety.get("blocking") or [])[:8],
        # Present only when an authoritative artifact already made a materiality call.
        # The desk never writes one of these and never infers one.
        "owner_materiality_decision": decision or {},
    }


def publish_state(run_dir: pathlib.Path) -> tuple:
    """(state, reason). Asked of the existing publisher, not decided here.

    publish_retained_fast_lane.resume(publish=False) loads and cross-validates every
    retained artifact, evaluates the real publication-safety bridge and returns either
    ELIGIBLE_NOT_PUBLISHED or BLOCKED with an exact named reason. It writes nothing,
    makes no model call and reaches no network: the fact check it consults is the one
    the run already recorded.

    Every failure mode -- import error, unreadable artifact, an exception inside the
    validator -- resolves to PUBLISH_BLOCKED. The desk fails closed on publication in
    exactly the way it refuses to fail closed on visibility.
    """
    try:
        import publish_retained_fast_lane as PRFL
    except Exception as e:                                            # noqa: BLE001
        return PUBLISH_BLOCKED, "publish validator unavailable (%s)" % type(e).__name__
    try:
        r = PRFL.resume(str(run_dir), publish=False)
    except Exception as e:                                            # noqa: BLE001
        return PUBLISH_BLOCKED, "publish validator failed (%s: %s)" % (
            type(e).__name__, str(e)[:160])
    if r.get("status") == "ELIGIBLE_NOT_PUBLISHED":
        return PUBLISH_ELIGIBLE, "the publication-safety bridge grants eligibility"
    return PUBLISH_BLOCKED, str(r.get("blocker") or "the publisher refused")[:400]


def read_run(run_dir) -> dict:
    """Everything the desk knows about one retained run. Read-only."""
    run_dir = pathlib.Path(run_dir)
    text, source_file = article_text(run_dir)
    words = len(text.split())
    gates = gate_summary(run_dir)
    if not text or words < MIN_ARTICLE_WORDS:
        return {
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "state": UPSTREAM_FAILURE,
            "article_text": text,
            "words": words,
            "source_file": source_file,
            "gates": gates,
            # Named, not silent. A 40-word stub is still reported as a 40-word stub.
            "reason": ("no article was produced" if not text
                       else "only %d words were produced (floor %d)"
                            % (words, MIN_ARTICLE_WORDS)),
            "publish_state": PUBLISH_BLOCKED,
            "publish_reason": "no article to publish",
        }
    state, reason = publish_state(run_dir)
    return {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "state": REVIEWABLE_DRAFT,
        "article_text": text,
        "words": words,
        "source_file": source_file,
        "gates": gates,
        "reason": "",
        "publish_state": state,
        "publish_reason": reason,
    }


def run_prefixes(env: dict | None = None) -> tuple:
    """Which retained directories the desk considers.

    Scheduled production runs only, by default: the evidence root also holds several
    hundred replays, rehearsals, probes and rescue directories, and a desk that offered
    those would be noise rather than a desk. A comma-separated override exists so a
    hand-driven run -- an owner repair, a rescue, a one-off -- can be put in front of
    the editor without a code change.
    """
    raw = (env if env is not None else os.environ).get(
        "CRIPMINDS_DESK_RUN_PREFIXES", "") or ""
    extra = tuple(p.strip() for p in raw.split(",") if p.strip())
    return extra or ("production-",)


def scan(root=None, prefixes=None, limit: int = 40) -> list:
    """Retained runs, newest first. Directory listing only -- no artifact is opened."""
    prefixes = prefixes or run_prefixes()
    root = pathlib.Path(root or EVIDENCE_ROOT)
    if not root.is_dir():
        return []
    dirs = [d for d in root.iterdir()
            if d.is_dir() and any(d.name.startswith(p) for p in prefixes)]
    return sorted(dirs, key=lambda d: d.name, reverse=True)[:limit]


# ── reading blocks ──────────────────────────────────────────────────────────────────

# Telegram's own limit is 4096 characters. The block size below is an editorial choice
# rather than a technical one: two to three paragraphs is what a person reads in one
# glance on a phone, and a block that needed splitting would break the one thing this
# design depends on -- one block, one message id, one exact paragraph range.
BLOCK_MAX_PARAGRAPHS = 3
BLOCK_MAX_CHARS = 3200


def paragraphs(text: str) -> list:
    return [p.strip() for p in (text or "").split("\n\n") if p.strip()]


def split_blocks(text: str) -> list:
    """Reading blocks with stable ids and exact paragraph ranges.

    A single paragraph longer than the character budget becomes its own block rather
    than being cut mid-sentence: an over-long block is a readable message, and a block
    whose boundary falls inside a sentence is not.
    """
    paras = paragraphs(text)
    out, current, start = [], [], 1
    for i, p in enumerate(paras, start=1):
        candidate = current + [p]
        too_long = sum(len(x) + 2 for x in candidate) > BLOCK_MAX_CHARS
        if current and (too_long or len(candidate) > BLOCK_MAX_PARAGRAPHS):
            out.append({"paragraph_start": start, "paragraph_end": i - 1,
                        "text": "\n\n".join(current)})
            current, start = [p], i
        else:
            current = candidate
    if current:
        out.append({"paragraph_start": start, "paragraph_end": len(paras),
                    "text": "\n\n".join(current)})
    for n, b in enumerate(out, start=1):
        b["block_id"] = "b%02d" % n
        b["index"] = n
        b["of"] = len(out)
    return out


# ── turning a reading into an edit brief ────────────────────────────────────────────

def derived_signals(event_type: str, detail: str = "") -> list:
    """LEVEL 2 interpretation of a BUTTON. Never applied to the owner's own words.

    Free text is deliberately not classified here. A keyword rule over editorial prose
    would be a relation validator built from the sample that suggested it, and this
    project has already had one of those falsified. The raw sentence is evidence; a
    guess about which taxonomy bucket it belongs in is not, and the rewriter reads the
    sentence anyway.

    THE CLICK IS THE PRIMARY TRUTH AND THE SIGNAL IS DERIVED FROM IT, NEVER THE REVERSE.
    `TOO_DENSE` + `TOO_MANY_NAMES` is what the owner said; `INSTITUTIONAL_LOAD_TOO_HIGH`
    is this function's reading of it, and re-reading it differently later must not touch
    the stored press.
    """
    if detail:
        sig = DETAIL_SIGNALS.get(detail)
        return [sig] if sig else []
    sig = BUTTON_SIGNALS.get(event_type)
    return [sig] if sig else []


def _locus(ev: dict) -> str:
    a, b = ev.get("paragraph_start"), ev.get("paragraph_end")
    if a and b:
        return "paragraphs %d-%d" % (a, b) if a != b else "paragraph %d" % a
    return "the article as a whole"


def edit_brief(events: list, *, words: int = 0) -> str:
    """The rewrite instruction, assembled from the reading. Deterministic, no model.

    THE POINT OF THIS FUNCTION, stated because it is the whole premise of the desk:
    Jascha does not have to formulate the solution. "wtf suddenly all those
    institutions" is a complete and sufficient editorial instruction. Turning it into
    "delay institutional detail, slow idea velocity, preserve the opening" is the
    machine's job, and it happens here.

    The owner's words are quoted verbatim and attributed to their exact paragraph range.
    The derived instruction lines sit under a separate heading so a later reader can
    always tell what was said from what was inferred.
    """
    reading = [e for e in events
               if e.get("event_type") in BUTTON_SIGNALS
               or e.get("event_type") in ("FREE_TEXT_FEEDBACK", "FEEDBACK_DETAIL")]
    L = ["EDITORIAL OBSERVATION",
         "A reader read this article%s and reacted. What follows is what they said and "
         "where they said it." % (" (%d words)" % words if words else "")]
    if not reading:
        L.append("")
        L.append("No reader reaction was recorded.")
        return "\n".join(L)

    L.append("")
    for e in reading:
        where = _locus(e)
        if e.get("event_type") == "FREE_TEXT_FEEDBACK":
            L.append("%s -- the reader wrote:" % where)
            L.append("    %r" % (e.get("raw_feedback") or ""))
        elif e.get("event_type") == "FEEDBACK_DETAIL":
            L.append("%s -- %s, specifically: %s"
                     % (where, (e.get("metadata") or {}).get("of_action", "?"),
                        e.get("detail", "")))
        else:
            L.append("%s -- %s" % (where, e["event_type"]))
            if e.get("raw_feedback"):
                L.append("    %r" % e["raw_feedback"])

    instructions, seen = [], set()
    for e in reading:
        if e.get("event_type") == "FEEDBACK_DETAIL":
            line = DETAIL_INSTRUCTIONS.get(e.get("detail") or "", "")
        else:
            line = BUTTON_INSTRUCTIONS.get(e.get("event_type") or "", "")
        if not line:
            continue
        text = "%s: %s" % (_locus(e), line)
        if text not in seen:
            seen.add(text)
            instructions.append(text)
    free = [e for e in reading if e.get("event_type") == "FREE_TEXT_FEEDBACK"]

    L += ["", "REWRITE INSTRUCTION"]
    if instructions:
        L += ["  - " + t for t in instructions]
    if free:
        L.append("  - act on the reader's own words above. They describe the problem, "
                 "not the fix; work out the fix.")
    if not instructions and not free:
        L.append("  - no change requested")

    # The factual boundary, restated in the brief itself rather than left to the caller.
    # An editorial rewrite rearranges what is already licensed; it does not research.
    L += ["",
          "FACTUAL BOUNDARY -- absolute",
          "  Reorder, cut, compress, expand explanation within what the article already "
          "says, improve transitions, change rhythm.",
          "  Add no fact, no causal relation, no motive, no chronology, no identity "
          "attribute, no mechanism, no scene, no quote, no testimony.",
          "  Every name, number, date and quotation must already appear in the text you "
          "were given."]
    return "\n".join(L)


# ── presentation ────────────────────────────────────────────────────────────────────

def status_line(run: dict) -> str:
    """One line of plain language. No SHAs, no gate taxonomy, no prompt hashes -- those
    live behind /debug, per the rule that the machine's problems must not become the
    owner's working interface."""
    if run["state"] == UPSTREAM_FAILURE:
        return "No article: %s" % run["reason"]
    if run["publish_state"] == PUBLISH_ELIGIBLE:
        return "Ready to publish"
    stage = run["gates"].get("failure_stage") or ""
    if stage:
        return "Readable now. Publication blocked at %s." % stage.title()
    return "Readable now. Publication blocked."


def survey(limit: int = 40) -> dict:
    """The product-health number this whole layer exists to move.

    FINISHED ARTICLE -> DESK DELIVERED is deliberately not a gate and is never used to
    decide anything. It is the one measurement that says whether the bureaucracy is
    still destroying work before a person sees it.
    """
    runs = [read_run(d) for d in scan(limit=limit)]
    readable = [r for r in runs if r["state"] == REVIEWABLE_DRAFT]
    return {
        "runs_examined": len(runs),
        "finished_articles": len(readable),
        "publishable_now": len([r for r in readable
                                if r["publish_state"] == PUBLISH_ELIGIBLE]),
        "no_article": len(runs) - len(readable),
        "words_written_unread": sum(r["words"] for r in readable),
        "held_at": _count_by_stage(readable),
    }


def _count_by_stage(runs: list) -> dict:
    out: dict = {}
    for r in runs:
        stage = r["gates"].get("failure_stage") or "none"
        out[stage] = out.get(stage, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="read-only survey of retained runs")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--list", action="store_true", help="one line per run")
    a = ap.parse_args()
    if a.list:
        for d in scan(limit=a.limit):
            r = read_run(d)
            print("%-46s %-18s %5d words  %s"
                  % (r["run_id"][:46], r["state"], r["words"], status_line(r)))
    print(json.dumps(survey(a.limit), indent=2))


# ── what the rewriter is allowed to know ────────────────────────────────────────────

MAX_EVIDENCE_FACTS = 60


def licensed_evidence(run_dir) -> list:
    """The run's own frozen Ledger propositions -- the facts this article was licensed
    to use, including the ones it did not use.

    THE MISSING INPUT, 2026-09-27. The rewriter used to receive the article and the
    reader's reaction and nothing else. Asked to give a passage more room, it had no
    licensed material to give it, and no way to tell a fact it had simply not used from
    a fact that does not exist. So it invented. Handing it the Ledger does not loosen
    the factual boundary; it is what makes the boundary satisfiable.

    Read-only, no network, no model. An unreadable or absent Ledger returns [] and the
    caller must then forbid expansion outright rather than proceed without evidence.
    """
    ledger = artifact(run_dir, "LEDGER.json")
    out = []
    for fid, fact in sorted((ledger or {}).items()):
        if not isinstance(fact, dict):
            continue
        prop = str(fact.get("proposition") or "").strip()
        if prop:
            out.append("%s  %s" % (fid, prop))
        if len(out) >= MAX_EVIDENCE_FACTS:
            break
    return out


REWRITE_SYSTEM = (
    "You are an editor making ONE pass over a finished article, acting on a reader's "
    "reaction. You are not the writer and you are not researching.\n"
    "\n"
    "HUMAN DOES NOT MEAN INVENTED. This is the whole of the job and the one rule that "
    "has been broken before.\n"
    "\n"
    "Human prose may come from: selection; pacing; paragraphing; reordering; staying "
    "longer with a concrete action the evidence already establishes; moving licensed "
    "material to where the reader wanted it; putting the person rather than the "
    "institution in the grammatical subject; letting a fact sit instead of stacking "
    "the next one behind it.\n"
    "\n"
    "Human prose may NEVER come from: sensory detail; scene texture; duration or "
    "repetition the evidence does not state; physical placement; motives; beliefs; "
    "implied dialogue; invented chronology; a new causal or administrative join "
    "between facts that are separate in the evidence; or metaphor that attributes an "
    "experience, feeling or belief to a real person.\n"
    "\n"
    "You may use any fact in the LICENSED EVIDENCE below, including ones the article "
    "has not used. You may use nothing else. If the reader asked for more and no "
    "licensed material answers it, leave the passage alone and say nothing about it.\n"
    "\n"
    "Reply with the rewritten article and nothing else -- no preamble, no notes, no "
    "explanation of what you changed."
)


def rewrite_user(article_text: str, brief: str, evidence: list) -> str:
    """The rewriter's whole world: the reaction, the licensed facts, the article."""
    L = [brief, ""]
    if evidence:
        L += ["LICENSED EVIDENCE -- the frozen facts this article was written from.",
              "You may draw on any of these, including facts the article has not used. "
              "You may use nothing outside this list and the article itself.", ""]
        L += ["  " + e for e in evidence]
    else:
        L += ["LICENSED EVIDENCE: none was retained for this article.",
              "You therefore may not expand anything. Work only by selection, "
              "reordering, pacing and paragraphing of the text you were given."]
    L += ["", "THE ARTICLE", "", article_text]
    return "\n".join(L)
