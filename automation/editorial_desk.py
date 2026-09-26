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

# Reader reactions, and the machine's reading of each. LEVEL 2 -- an interpretation of an
# unambiguous button the owner chose on purpose, recomputable later, and carrying no
# authority over anything. The owner's own words are never passed through this.
BUTTON_SIGNALS = {
    "CONTINUE": "READ_THROUGH_NO_OBJECTION",
    "TOO_FAST": "IDEA_VELOCITY_TOO_HIGH",
    "WHY_NOW": "READER_PURPOSE_LOST",
    "STRONG": "STRONG_PASSAGE",
    "READER_LOST": "READER_DISENGAGED",
    "WANT_MORE": "WANTS_MORE_ON_CONSEQUENCE",
}

# What each button asks the rewriter to do. Bounded, and every line is a constraint on
# arrangement rather than on content -- see the prohibition at the end of edit_brief().
BUTTON_INSTRUCTIONS = {
    "TOO_FAST": "slow the idea velocity here: fewer new named entities per paragraph, "
                "and let one idea land before the next arrives",
    "WHY_NOW": "make clear why the reader is being told this, here, before telling it",
    "READER_LOST": "this is where the reader left. Rebuild the thread into this passage "
                   "or cut what broke it",
    "WANT_MORE": "give this more room -- the reader wanted to stay here",
    "STRONG": "preserve this passage. Do not rewrite it, do not compress it, do not "
              "move it later",
    "CONTINUE": "",
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

def derived_signals(event_type: str) -> list:
    """LEVEL 2 interpretation of a BUTTON. Never applied to the owner's own words.

    Free text is deliberately not classified here. A keyword rule over editorial prose
    would be a relation validator built from the sample that suggested it, and this
    project has already had one of those falsified. The raw sentence is evidence; a
    guess about which taxonomy bucket it belongs in is not, and the rewriter reads the
    sentence anyway.
    """
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
               or e.get("event_type") == "FREE_TEXT_FEEDBACK"]
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
        else:
            L.append("%s -- %s" % (where, e["event_type"]))
            if e.get("raw_feedback"):
                L.append("    %r" % e["raw_feedback"])

    instructions, seen = [], set()
    for e in reading:
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
