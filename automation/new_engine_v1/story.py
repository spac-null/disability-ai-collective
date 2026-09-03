"""
story.py -- story intelligence, kept apart from research intelligence and from prose.

WHY THIS EXISTS (measured, 2026-09-03, see .claude/story-architecture/):

The Writer was handed 5,554-7,121 prompt words to produce a ~650-word article: 15-18
mentions of "source", 27-32 source-ID markers, 11-16 verified-excerpt blocks, and the
whole research apparatus. It reproduced the apparatus, because the apparatus was what it
was given. The clearest instance is mechanical rather than stylistic -- `evidence_gaps`
and `grounding_boundaries` are MACHINE CONSTRAINTS that reached the Writer as CONTENT,
and came back as sentences:

  given:  "The source does not describe how any visitor actually perceived these spaces"
  became: "It does not report what any visitor experienced, and I am not claiming it does."

  given:  "The anchor does not describe the physical form of the building, its site"
  became: "It does not describe the building's form, its site, or any actual device..."

Grounding V2's shadow observations had been reporting the same defect from the other
side: 7 of its UNSUPPORTED findings were exactly these negative-existence sentences,
which no evidence can support because they are claims about what evidence lacks.

So the fix is not a phrase blacklist. A prohibition must bound the GENERATOR and never
be handed to it as something to write about. That is the one invariant this module
enforces mechanically; everything else here is contract.

THE DOCTRINE, stated once:
    THE VALUE OF RESEARCH IS NOT MEASURED BY HOW MUCH OF IT APPEARS IN THE ARTICLE.
"""
from __future__ import annotations

import re

# ── outcomes ──────────────────────────────────────────────────────────────────
NO_STORY = "NO_STORY"
BRIEF_ONLY = "BRIEF_ONLY"

SUPPORTED_CAUSAL = "SUPPORTED_CAUSAL"
CHRONOLOGICAL_ADJACENCY = "CHRONOLOGICAL_ADJACENCY"
CONTESTED = "CONTESTED"
LINK_KINDS = (SUPPORTED_CAUSAL, CHRONOLOGICAL_ADJACENCY, CONTESTED)

STRONG_DIRECT_LENS = "STRONG_DIRECT_LENS"
STRONG_INTERPRETIVE_LENS = "STRONG_INTERPRETIVE_LENS"
WEAK_ANALOGY = "WEAK_ANALOGY"
NO_PLAUSIBLE_LENS = "NO_PLAUSIBLE_LENS"
WRONG_PUBLICATION = "GREAT_GENERAL_STORY_WRONG_PUBLICATION"
LENS_VERDICTS = (STRONG_DIRECT_LENS, STRONG_INTERPRETIVE_LENS, WEAK_ANALOGY,
                 NO_PLAUSIBLE_LENS, WRONG_PUBLICATION)
LENS_PUBLISHABLE = (STRONG_DIRECT_LENS, STRONG_INTERPRETIVE_LENS)

NARRATIVE_ARTICLE = "NARRATIVE_ARTICLE"
SHORT_NARRATIVE = "SHORT_NARRATIVE"
BRIEF = "BRIEF"
HOLD_NO_STORY = "HOLD_NO_STORY"
HOLD_WRONG_PUBLICATION = "HOLD_WRONG_PUBLICATION"
ARTICLE_TYPES = (NARRATIVE_ARTICLE, SHORT_NARRATIVE, BRIEF,
                 HOLD_NO_STORY, HOLD_WRONG_PUBLICATION)

CARRIERS = ("person", "object", "event", "place", "process")

CUT_REASONS = ("REDUNDANT_PROOF", "BACKGROUND_NOT_NEEDED", "SECOND_EXAMPLE_SAME_POINT",
               "NAME_OVERLOAD", "CONCEPT_OVERLOAD", "BREAKS_STORY_MOMENTUM",
               "PROVENANCE_ONLY", "MACHINE_BOUNDARY_ONLY", "INTERESTING_BUT_WRONG_STORY")

# ── the enforced invariant ────────────────────────────────────────────────────
# Constructions that describe the RESEARCH rather than the world. These may not appear
# anywhere in a writer packet. The bare word "source" is NOT here: a newspaper's own
# source can be story material, and banning the word would be the phrase-blacklist
# mistake the brief rules out. What is banned is the auditing frame.
PROVENANCE_FRAMES = [
    r"\bthe source\b", r"\bthe anchor\b", r"\bthe brief\b", r"\bthe evidence\b",
    r"\bthe material\b", r"\bthe research pack\b", r"\bthis reading\b",
    r"\baccording to the source\b",
    r"\bdoes not (?:establish|say|state|tell|report|describe|show|prove)\b",
    r"\bno such claim\b", r"\bnothing in the (?:source|anchor|evidence)\b",
    r"\bcontains no\b", r"\bgives none\b", r"\bis not supported by\b",
    r"\bS\d+\b",                                  # source-id markers
    r"\b(?:ANCHOR|PRIMARY|INDEPENDENT|TERTIARY)\b",   # role taxonomy
    r"\bsha256\b", r"\bprovenance\b", r"\bverified excerpt\b",
]
# Scaffold names that must never reach prose (campaign brief section 39).
SCAFFOLD_NAMES = ["STORY_SPINE", "CRIP_TURN", "USE_FACTS", "USE_QUOTES", "USE_PEOPLE",
                  "USE_CONCEPTS", "CUT_EVIDENCE", "BEAT_", "ENDING_MOVE",
                  "READER_INITIAL_STATE", "OPENING_OBJECT", "ARTICLE_TYPE",
                  "narrative_yield", "carrier_type", "story_id"]


def leaks(text: str) -> list:
    """Every provenance frame present in `text`, with counts. Empty list means clean."""
    out = []
    for p in PROVENANCE_FRAMES:
        n = len(re.findall(p, text, re.I))
        if n:
            out.append((p.replace(r"\b", "").replace(r"(?:", "(").replace(r"\d+", "N"), n))
    return sorted(out, key=lambda x: -x[1])


def scaffold_leaks(text: str) -> list:
    return sorted({n for n in SCAFFOLD_NAMES if n.lower() in text.lower()})


# ── STORY FINDER ──────────────────────────────────────────────────────────────
# Penalised openers: an article whose movement is "this reveals / this reframes" has an
# argument, not a story. Diagnostic weight, not a ban -- the idea still has to ride on
# something concrete.
CONCEPT_MOVES = [r"\bthis reveals\b", r"\bthis reframes\b", r"\bthis complicates\b",
                 r"\bwhat becomes visible\b", r"\bshifts the job\b",
                 r"\binvites us to\b", r"\basks us to\b", r"\breminds us\b"]


def narrative_yield(cand: dict) -> dict:
    """Score a story candidate on what a reader can actually follow.

    Deliberately crude and deliberately explainable: the components are reported so a
    human can disagree with the arithmetic rather than being handed one number.
    """
    c = {}
    c["carrier"] = 2 if cand.get("carrier_type") in CARRIERS else 0
    c["concrete_opening"] = 2 if (cand.get("opening_possibility") or "").strip() else 0
    c["real_change"] = 2 if (cand.get("real_event_or_change") or "").strip() else 0
    links = cand.get("causal_chain") or []
    c["causal"] = 2 if any(l.get("kind") == SUPPORTED_CAUSAL for l in links) else (
        1 if links else 0)
    c["tension"] = 2 if (cand.get("tension") or "").strip() else 0
    c["discovery"] = 1 if ((cand.get("reader_first_sees") or "").strip()
                           and (cand.get("reader_later_discovers") or "").strip()) else 0
    spine = cand.get("central_subject", "") + " " + (cand.get("tension") or "")
    c["concept_only_penalty"] = -2 if any(
        re.search(p, spine, re.I) for p in CONCEPT_MOVES) else 0
    c["no_evidence_penalty"] = -3 if not (cand.get("evidence_ids") or []) else 0
    return {"components": c, "score": sum(c.values()), "max": 11}


def validate_candidate(cand: dict) -> list:
    errs = []
    if not (cand.get("story_id") or "").strip():
        errs.append("story_id missing")
    if cand.get("carrier_type") not in CARRIERS:
        errs.append("carrier_type %r not in %s" % (cand.get("carrier_type"), CARRIERS))
    if not (cand.get("evidence_ids") or []):
        errs.append("no evidence_ids: a story with no evidence is not a story")
    for l in (cand.get("causal_chain") or []):
        if l.get("kind") not in LINK_KINDS:
            errs.append("causal link kind %r not in %s" % (l.get("kind"), LINK_KINDS))
        if l.get("kind") == SUPPORTED_CAUSAL and not (l.get("evidence_ids") or []):
            errs.append("SUPPORTED_CAUSAL link without evidence -- chronology is not cause")
    return errs


# ── CRIP MINDS WORTH GATE ─────────────────────────────────────────────────────
# Formulations that do not do intellectual work. A lens must change what the story
# MEANS; these merely attach a vocabulary to it.
EMPTY_LENS = [r"\bfaces? barriers\b", r"\bremind(?:s|er)? us that\b",
              r"\babout (?:difference|imperfection|friction)\b",
              r"\bdisabled people (?:face|experience|encounter)\b",
              r"\bis a metaphor for\b", r"\blike a disability\b",
              r"\bjust as disabled\b", r"\bwe are all\b"]


def validate_lens(lens: dict) -> list:
    """A publishable lens must name a mechanism and cite evidence, not gesture."""
    errs = []
    v = lens.get("verdict")
    if v not in LENS_VERDICTS:
        return ["verdict %r not in %s" % (v, LENS_VERDICTS)]
    if v not in LENS_PUBLISHABLE:
        return errs                      # a refusal needs no further proof
    claim = (lens.get("lens_claim") or "").strip()
    if len(claim) < 40:
        errs.append("lens_claim too thin to do interpretive work (%d chars)" % len(claim))
    if not (lens.get("evidence_ids") or []):
        errs.append("a publishable lens must cite evidence")
    if not (lens.get("changes_meaning_how") or "").strip():
        errs.append("lens does not say what it changes about the story's meaning")
    for p in EMPTY_LENS:
        if re.search(p, claim, re.I):
            errs.append("lens_claim uses an empty formulation: %s"
                        % p.replace(r"\b", ""))
    return errs


# ── STORY ARCHITECT ───────────────────────────────────────────────────────────
def validate_architecture(arch: dict, evidence_ids: set) -> list:
    """The architecture is the reader's path. Checked for shape and for honesty about
    which evidence it intends to use -- and to CUT."""
    errs = []
    if arch.get("article_type") not in ARTICLE_TYPES:
        errs.append("article_type %r not in %s" % (arch.get("article_type"), ARTICLE_TYPES))
    if arch.get("article_type") in (HOLD_NO_STORY, HOLD_WRONG_PUBLICATION):
        return errs                      # a hold needs no beats
    spine = (arch.get("story_spine") or "").strip()
    if not spine:
        errs.append("story_spine missing")
    elif len(spine.split(".")) > 3:
        errs.append("story_spine is not one sentence")
    if not (arch.get("opening_object_or_event") or "").strip():
        errs.append("opening_object_or_event missing -- openings must be concrete")
    beats = arch.get("beats") or []
    if len(beats) < 2:
        errs.append("fewer than 2 beats is not a path through a story")
    seen = set()
    for i, b in enumerate(beats, 1):
        bid = b.get("beat_id")
        if not bid or bid in seen:
            errs.append("beat %d has a missing or duplicate beat_id" % i)
        seen.add(bid)
        if not (b.get("concrete_carrier") or "").strip():
            errs.append("%s has no concrete carrier" % bid)
        if not (b.get("why_reader_wants_next") or "").strip() and i < len(beats):
            errs.append("%s does not earn the next beat" % bid)
        for f in (b.get("facts_allowed") or []):
            if f not in evidence_ids:
                errs.append("%s allows fact %s that is not in the frozen evidence" % (bid, f))
    if not (arch.get("ending_move") or "").strip():
        errs.append("ending_move missing")
    # USE/CUT honesty
    use = set(arch.get("use_facts") or [])
    unknown = use - evidence_ids
    if unknown:
        errs.append("use_facts not in evidence: %s" % sorted(unknown))
    cut = arch.get("cut_evidence") or []
    for c in cut:
        if c.get("reason") not in CUT_REASONS:
            errs.append("cut reason %r not in the declared set" % c.get("reason"))
    if not cut:
        errs.append("no cut_evidence: selection that discards nothing is not selection")
    cut_ids = {c.get("evidence_id") for c in cut}
    both = use & cut_ids
    if both:
        errs.append("evidence both used and cut: %s" % sorted(both))
    # every beat's facts must be declared in use_facts
    for b in beats:
        for f in (b.get("facts_allowed") or []):
            if f not in use:
                errs.append("%s uses %s which is not in use_facts" % (b.get("beat_id"), f))
    return errs


# ── WRITER PACKET ─────────────────────────────────────────────────────────────
def build_packet(arch: dict, lens: dict, facts: dict, quotes: dict | None = None) -> dict:
    """The minimal writing packet.

    What is deliberately ABSENT is the point: no research pack bodies, no source roles,
    no provenance, no evidence_gaps, no grounding-boundary prose. Prohibitions travel in
    `prohibitions`, which `render()` turns into imperatives ("Do not name...") rather
    than descriptions of what the evidence lacks -- so there is nothing for the Writer to
    convert into a caveat sentence.
    """
    quotes = quotes or {}
    use = list(arch.get("use_facts") or [])
    return {
        "article_type": arch.get("article_type"),
        "story_spine": arch.get("story_spine", ""),
        "opening": arch.get("opening_object_or_event", ""),
        "reader_initial_state": arch.get("reader_initial_state", ""),
        "beats": [{"beat_id": b.get("beat_id"),
                   "happens": b.get("happens", ""),
                   "carrier": b.get("concrete_carrier", ""),
                   "facts": [facts[f] for f in (b.get("facts_allowed") or []) if f in facts],
                   "concept": b.get("concept_introduced", ""),
                   "withhold": b.get("must_not_say_yet", "")}
                  for b in (arch.get("beats") or [])],
        "turn": arch.get("turn", ""),
        "crip_turn": arch.get("crip_turn", ""),
        "lens": lens.get("lens_claim", "") if lens.get("verdict") in LENS_PUBLISHABLE else "",
        "ending_move": arch.get("ending_move", ""),
        "facts": [facts[f] for f in use if f in facts],
        "quotes": [quotes[q] for q in (arch.get("use_quotes") or []) if q in quotes],
        "definitions": arch.get("definitions") or {},
        "prohibitions": list(arch.get("prohibitions") or []),
        "_cut_count": len(arch.get("cut_evidence") or []),
    }


def render(packet: dict) -> str:
    """The prompt. Prohibitions are imperatives to the generator; nothing here describes
    the state of the evidence."""
    L = ["You are writing one finished article. Everything you need is below.", ""]
    L.append("WHAT THE STORY IS")
    L.append("  " + packet["story_spine"])
    L.append("")
    L.append("OPEN ON")
    L.append("  " + packet["opening"])
    if packet["reader_initial_state"]:
        L.append("  The reader should first understand only this: "
                 + packet["reader_initial_state"])
    L.append("")
    L.append("THE PATH, IN ORDER")
    for i, b in enumerate(packet["beats"], 1):
        L.append("  %d. %s" % (i, b["happens"]))
        if b["carrier"]:
            L.append("     carried by: %s" % b["carrier"])
        for f in b["facts"]:
            L.append("     - %s" % f)
        if b["concept"]:
            L.append("     explain plainly, once, here: %s" % b["concept"])
        if b["withhold"]:
            L.append("     not yet: %s" % b["withhold"])
    L.append("")
    if packet["turn"]:
        L.append("THE TURN")
        L.append("  " + packet["turn"])
        L.append("")
    if packet["crip_turn"]:
        L.append("WHERE THE MEANING CHANGES")
        L.append("  " + packet["crip_turn"])
        if packet["lens"]:
            L.append("  The idea that does this work: " + packet["lens"])
        L.append("")
    if packet["quotes"]:
        L.append("QUOTE EXACTLY, OR NOT AT ALL")
        for q in packet["quotes"]:
            L.append('  "%s"' % q)
        L.append("")
    if packet["definitions"]:
        L.append("EXPLAIN AT FIRST USE")
        for k, v in packet["definitions"].items():
            L.append("  %s -- %s" % (k, v))
        L.append("")
    L.append("END ON")
    L.append("  " + packet["ending_move"])
    L.append("")
    L.append("RULES")
    L.append("  Write only what is above. Do not add facts, names, numbers, dates,")
    L.append("  places or quotations that do not appear here.")
    L.append("  Do not discuss what is known or unknown about this story, and do not")
    L.append("  qualify it. If something is not above, it simply does not appear.")
    L.append("  Do not write about documents or reporting unless a document is itself")
    L.append("  part of what happens.")
    L.append("  One difficult idea at a time. Give each paragraph one job.")
    for p in packet["prohibitions"]:
        L.append("  " + (p if p.lower().startswith(("do not", "never", "avoid"))
                         else "Do not " + p))
    return "\n".join(L)


def validate_packet(packet: dict) -> list:
    """Fail closed. A packet carrying the auditing frame would reintroduce the very
    defect this module exists to remove, so it is refused rather than cleaned."""
    errs = []
    text = render(packet)
    for frame, n in leaks(text):
        errs.append("packet carries a provenance frame %r x%d" % (frame, n))
    for s in scaffold_leaks(text):
        errs.append("packet exposes the scaffold name %r" % s)
    if not (packet.get("story_spine") or "").strip():
        errs.append("packet has no story spine")
    if not (packet.get("beats") or []):
        errs.append("packet has no beats")
    if not (packet.get("ending_move") or "").strip():
        errs.append("packet has no ending move")
    for p in (packet.get("prohibitions") or []):
        if re.search(r"\bdoes not\b|\bno such\b|\bcontains no\b", p, re.I):
            errs.append("prohibition %r is phrased as a description of the evidence, "
                        "which is what becomes a caveat sentence" % p[:60])
    return errs


# ── POST-WRITER: was the selection actually obeyed? ───────────────────────────
# Loop 1 of the 2026-09-03 campaign produced the finding that motivated this function.
# The architecture removed the research machinery from the prose completely (leakage
# 10 -> 0, essay moves 3 -> 0, names 38 -> 15) and the Writer then introduced four
# things that were not in its packet:
#
#   "the ears"                 traceable only to a fact the architect had CUT
#   "The pavilions are gone"   contradicted evidence saying one would be relocated
#   "pink" wall                no such word in the frozen evidence
#   "the floor sat lower"      an invented physical arrangement
#
# So a declared CUT list is not a control. Selection has to be CHECKED after writing,
# the way coverage is checked after grounding -- otherwise the architecture trades
# visible hedging for invisible embellishment, which is the worse of the two because a
# reader cannot see it.
#
# This is a deterministic screen, not a grounder. It reports suspicion for a human or
# the real Grounder to settle, and it never edits prose.
CUT_SENTINEL_MIN = 4          # ignore very short tokens; they collide with ordinary words


def cut_adherence(article_text: str, arch: dict, cut_terms: dict | None = None) -> dict:
    """Which CUT items show up in the finished prose anyway?

    `cut_terms` maps a cut evidence_id to the concrete words that would betray it in
    prose (an id like TOPENG_BUDUH_MASK_COUNT is not itself searchable). Terms are
    supplied by the architect stage, so this stays evidence-driven rather than a
    hardcoded vocabulary.
    """
    cut_terms = cut_terms or {}
    body = " ".join(article_text.split()).lower()
    violations, skipped, unwatched = [], [], []
    for c in (arch.get("cut_evidence") or []):
        cid = c.get("evidence_id")
        terms = cut_terms.get(cid) or []
        if not terms:
            unwatched.append(cid)
        for term in terms:
            t = term.strip().lower()
            if len(t) < CUT_SENTINEL_MIN:
                # Reported, never silently dropped. In loop 1 the term "ear" was
                # discarded by this very threshold and the check returned OK on an
                # article containing "the ears" -- a screen that quietly disables part
                # of itself is worse than no screen.
                skipped.append({"evidence_id": cid, "term": term})
                continue
            if t in body:
                violations.append({"evidence_id": cid, "reason": c.get("reason"),
                                   "term": term})
    return {"violations": violations,
            "ok": not violations and not skipped and not unwatched,
            "clean_prose": not violations,
            "skipped_too_short": skipped,
            "cut_without_watch_terms": unwatched,
            "cut_declared": len(arch.get("cut_evidence") or [])}


def scaffold_adherence(article_text: str) -> dict:
    """Machine scaffold names must never surface in prose (campaign brief section 39)."""
    found = scaffold_leaks(article_text)
    return {"leaked": found, "ok": not found}


def prose_leaks(article_text: str) -> dict:
    """The reader-facing measure this whole module exists to move."""
    found = leaks(article_text)
    return {"frames": found, "total": sum(n for _, n in found), "ok": not found}
