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
    # "the material" alone is ordinary English -- a telescope's data is material, and a
    # pavilion is made of materials. Only the auditing construction is a leak, the same
    # way the bare word "source" is not banned.
    r"\bthe material (?:does not|gives|establishes|shows|says|contains)\b",
    r"\bthe research pack\b", r"\bthis reading\b",
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


# ── VARIANT B: the factual surface must be traceable to approved facts ────────
# Loop 1's four defects were "the ears" (a CUT fact), "pink" (a colour absent from all
# evidence), "the pavilions are gone" (contradicting evidence) and an invented floor
# level. Only the first is catchable by watching CUT terms. The other three are
# ATTRIBUTES the packet never granted, so the screen that catches them has to work the
# other way round: every content word in the prose that the packet does not contain is a
# candidate addition.
#
# This is a candidate generator, not a verdict. Prose legitimately adds connective and
# ordinary vocabulary, so the output needs a human or the Grounder to settle. What it
# guarantees is that an invented attribute cannot pass unnoticed merely because the
# Writer was told not to invent one.
_FUNCTION_WORDS = set("""
a an the and or but nor so yet for if then than that this these those there here it its
is are was were be been being do does did doing have has had having will would can could
shall should may might must of in on at to from by with about into over under again
further once all any both each few more most other some such no not only own same too
very as up down out off above below between through during before after while because
until against among around also just now still even ever never always often sometimes
they them their he she his her you your we our i me my one two three four five six seven
eight nine ten what which who whom when where why how much many said says say get got
make made take took come came go went know knew think thought see saw look looked
part way thing things something anything nothing everything someone anyone
""".split())

# Prose the packet cannot supply and a reader cannot check: high-risk additions worth
# surfacing separately even when they look ordinary.
SENSORY_RISK = ("pink", "red", "blue", "green", "yellow", "white", "black", "grey",
                "gray", "brown", "golden", "warm", "cold", "cool", "hot", "damp", "dry",
                "loud", "quiet", "silent", "bright", "dark", "smooth", "rough", "soft",
                "hard", "sweet", "bitter", "salty", "sour", "fragrant", "acrid")


def _content_words(text: str) -> set:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", text.lower())
    return {w for w in words if w not in _FUNCTION_WORDS}


def _numbers(text: str) -> set:
    return set(re.findall(r"\b\d[\d,.]*\b", text))


def _entities(text: str, skip_sentence_initial: bool = True) -> set:
    """Capitalised tokens. Sentence-initial ones are skipped when reading PROSE, because
    every sentence starts with a capital; they are NOT skipped when building the approved
    set, or a name that happens to open a packet line looks unapproved in the article.
    That false positive was real: "Jia" and "Jakarta" both open packet lines."""
    out = set()
    for s in re.split(r"(?<=[.!?])\s+", text):
        toks = re.findall(r"\b[A-Z][A-Za-z'’.-]{2,}\b", s)
        for tok in (toks[1:] if skip_sentence_initial else toks):
            tok = tok.rstrip(".,")
            out.add(tok)
            out.add(re.sub(r"['’]s$", "", tok))          # Curated's -> Curated
            for part in re.split(r"[-.]", tok):          # Jakarta-based -> Jakarta
                if len(part) > 2:
                    out.add(part)
    return out


def factual_surface_audit(article_text: str, packet: dict) -> dict:
    """What factual surface does the prose carry that the packet never granted?

    Three channels, in descending order of how much a reader should trust them:
      numbers   -- a figure not in the packet is almost always an addition
      entities  -- a capitalised name not in the packet is almost always an addition
      terms     -- content words absent from the packet; noisy, ranked as candidates
      sensory   -- the subset of those that assert a perceivable property
    """
    approved = render(packet)
    a_words, a_nums, a_ents = (_content_words(approved), _numbers(approved),
                               _entities(approved, skip_sentence_initial=False))
    body = article_text.split("---", 2)[2] if article_text.startswith("---") else article_text
    body = re.sub(r"^#\s+.*\n", "", body.strip(), count=1)

    nums = sorted(_numbers(body) - a_nums)
    ents = sorted(_entities(body) - a_ents)
    terms = sorted(_content_words(body) - a_words)
    sensory = sorted(t for t in terms if t in SENSORY_RISK)
    scene = sorted(t for t in terms if t in SCENE_RISK)
    return {"unapproved_numbers": nums,
            "unapproved_entities": ents,
            "unapproved_sensory": sensory,
            "unapproved_scene": scene,
            "unapproved_terms_count": len(terms),
            "unapproved_terms_sample": terms[:25],
            "hard_ok": not nums and not ents and not sensory and not scene,
            "note": "terms are candidates for review, not violations; numbers, entities "
                    "sensory assertion and scene vocabulary are hard signals"}


# ── LOOP 3: the lens must be EMBODIED, not asserted ──────────────────────────
# Four independent blind readers, across two unrelated subjects, converged on the same
# criticism of the new architecture's output:
#
#   "written in the passive-universal -- no body, no name, no incident. It is the thesis
#    paragraph and it is the only paragraph with nobody in it."
#   "a single late, abstract aside ... should be seeded earlier and in something as
#    physical as the salt."
#   "nothing in the piece is written from disability experience. The teacher is a
#    placeholder where a person should be."  (crip fit 2/5)
#   "because the lens never surfaces, an editor could reasonably file this as a smart
#    access-policy column. Fit is earned, not asserted."  (crip fit 3/5)
#
# So a lens claim is not enough, and neither is citing evidence for it. The turn has to
# reinterpret something the reader has ALREADY BEEN SHOWN. That is checkable: the
# crip_turn must reach back to a carrier or fact from an earlier beat, and the lens's
# evidence must overlap the evidence the beats actually used.
#
# One further signal from the same readers: "The teacher is invented -- an unreported,
# unnamed hypothetical carrying the entire payload of the piece." Scene vocabulary is
# therefore promoted to a hard signal in the factual surface audit, alongside sensory
# assertion. The screen had surfaced "laptop", "room", "somewhere", "waiting" as
# candidates; nobody looked. A signal nobody looks at is not a control.
SCENE_RISK = ("laptop", "desk", "chair", "classroom", "kitchen",
              "window", "screen", "phone", "queue", "corridor", "doorway", "armchair",
              "sofa", "bedroom", "office")

GENERIC_SUBJECTS = [r"\banyone whose\b", r"\banyone who\b", r"\bpeople who\b",
                    r"\bthose who\b", r"\bsomeone whose\b", r"\ba person who\b",
                    r"\bwe all\b", r"\beveryone who\b"]


def validate_lens_embodiment(arch: dict, lens: dict) -> list:
    """The crip turn must land on something the reader has already been shown."""
    errs = []
    if lens.get("verdict") not in LENS_PUBLISHABLE:
        return errs
    turn = (arch.get("crip_turn") or "").strip()
    if not turn:
        return ["crip_turn missing while the lens is publishable"]

    beats = arch.get("beats") or []
    earlier_facts, carriers = set(), []
    for b in beats:
        earlier_facts |= set(b.get("facts_allowed") or [])
        if (b.get("concrete_carrier") or "").strip():
            carriers.append(b["concrete_carrier"])

    # The relation is DECLARED, not inferred. A first version of this check inferred it
    # from token overlap between the turn and any beat carrier, and passed both
    # architectures that four blind readers had criticised for exactly this -- one match
    # was the word "named". A proxy that lenient is not a check, so the architect now has
    # to say which beat the turn re-reads, and the turn has to name that beat's carrier.
    rereads = (arch.get("crip_turn_rereads") or "").strip()
    if not rereads:
        errs.append("crip_turn_rereads missing: the turn must declare which earlier beat "
                    "it reinterprets, or it is an aside rather than a turn")
        return errs
    target = [b for b in beats if b.get("beat_id") == rereads]
    if not target:
        errs.append("crip_turn_rereads names %r, which is not a beat" % rereads)
        return errs
    if target[0] is beats[-1] and len(beats) > 1:
        errs.append("the turn re-reads the final beat, so it reinterprets nothing the "
                    "reader has had time to settle into")
    tnouns = {w for w in re.findall(r"[a-z]{4,}",
                                    (target[0].get("concrete_carrier") or "").lower())
              if w not in _FUNCTION_WORDS}
    if tnouns and not any(n in turn.lower() for n in tnouns):
        errs.append("the turn does not name anything from %s, the beat it claims to "
                    "re-read (expected one of %s)" % (rereads, sorted(tnouns)[:6]))

    # 1. the lens's evidence must be evidence the story actually showed
    lens_ev = set(lens.get("evidence_ids") or [])
    if lens_ev and not (lens_ev & earlier_facts):
        errs.append("the lens cites evidence the beats never show: %s"
                    % sorted(lens_ev - earlier_facts))

    # 2. the turn must reach back to a carrier the reader has met
    turn_l = turn.lower()
    nouns = set()
    for c in carriers:
        nouns |= {w for w in re.findall(r"[a-z]{4,}", c.lower())
                  if w not in _FUNCTION_WORDS}
    if nouns and not any(n in turn_l for n in nouns):
        errs.append("the crip turn names nothing the reader has already been shown "
                    "(no carrier noun from any beat appears in it)")

    # 3. it must not rest ONLY on a generic universal subject
    generic = [p.replace(r"\b", "") for p in GENERIC_SUBJECTS
               if re.search(p, turn, re.I)]
    if generic and not any(n in turn_l for n in nouns):
        errs.append("the crip turn rests on a generic subject (%s) with nothing concrete "
                    "in it" % ", ".join(generic))
    return errs



def architect_prose_audit(arch: dict, facts: dict, quotes: dict | None = None) -> dict:
    """The architect's own prose fields, checked against the approved facts.

    This exists because of a mistake made while running the campaign. "pink" was
    reported as a Writer fabrication; it was not. It had been written into the
    architecture's `turn` field by hand, and `factual_surface_audit` compares prose to
    the PACKET -- so the packet had already legitimised it. An audit whose ground truth
    is itself generated cannot detect a fabrication introduced upstream of it.

    Same three hard channels, applied one stage earlier.
    """
    quotes = quotes or {}
    evidence = " ".join(list(facts.values()) + list(quotes.values()))
    e_words, e_nums = _content_words(evidence), _numbers(evidence)
    e_ents = _entities(evidence, skip_sentence_initial=False)
    prose = " ".join(str(arch.get(k) or "") for k in
                     ("story_spine", "opening_object_or_event", "reader_initial_state",
                      "turn", "crip_turn", "ending_move"))
    for b in (arch.get("beats") or []):
        prose += " " + " ".join(str(b.get(k) or "") for k in
                                ("happens", "concrete_carrier", "concept_introduced"))
    terms = _content_words(prose) - e_words
    return {"unapproved_numbers": sorted(_numbers(prose) - e_nums),
            "unapproved_entities": sorted(_entities(prose) - e_ents),
            "unapproved_sensory": sorted(t for t in terms if t in SENSORY_RISK),
            "unapproved_scene": sorted(t for t in terms if t in SCENE_RISK),
            "hard_ok": not (sorted(_numbers(prose) - e_nums)
                            or sorted(_entities(prose) - e_ents)
                            or [t for t in terms if t in SENSORY_RISK]
                            or [t for t in terms if t in SCENE_RISK])}


# ── the blind spot the Roman ending exposed ───────────────────────────────────
# "the part that was not engineered" survived every screen. It is not an unapproved
# number, name, colour or scene prop -- it is a claim that something does not exist. No
# evidence can support an absence unless the evidence states the absence, and Grounding
# V2 had independently been reporting this same class as negative-existence findings it
# could not support.
#
# So negative shape is detected deterministically here, and each hit must then be matched
# to a ledger fact of the corresponding type. Detection is mechanical; the decision about
# whether a given sentence IS a claim stays with a reader or an evaluator, because regex
# cannot settle semantics. What this guarantees is that no such sentence passes unseen.
NEGATIVE_SHAPES = [
    (r"\bwas not (?:engineered|built|designed|tested|intended|planned)\b", "NEGATIVE_EXISTENCE"),
    (r"\b(?:nobody|no one|nothing) (?:had |has |was |is )?(?:built|made|designed|tested|engineered|written)\b", "NEGATIVE_EXISTENCE"),
    (r"\bthere (?:was|is|were|are) no\b", "NEGATIVE_EXISTENCE"),
    (r"\bno (?:such|way|means|method|record|evidence|provision)\b", "NEGATIVE_EXISTENCE"),
    (r"\bhas (?:never|not yet) been\b", "NEGATIVE_EXISTENCE"),
    (r"\bnever (?:happened|existed|been|occurred|tested)\b", "NEGATIVE_EXISTENCE"),
    (r"\bdoes not (?:exist|contain|include|mention|describe|show|address)\b", "ABSENCE"),
    (r"\bnothing (?:in|about|on)\b", "ABSENCE"),
    (r"\bonly\b(?=[^.]*\b(?:one|two|first|single|way|thing|part)\b)", "EXCLUSIVITY"),
    (r"\bnone of\b", "EXCLUSIVITY"),
    (r"\bthe (?:first|last|only) (?:ever|time|one|person|instrument)\b", "FIRST_LAST"),
    (r"\b(?:unlike|whereas) [^,.]{3,40}, [^.]{0,40}\b(?:did not|does not|had no)\b", "COMPARATIVE_NEGATION"),
    (r"\bno box on the form\b", "ABSENCE"),
]
# Intent, motive and causal assertions: the other classes a story is tempted to invent.
INTENT_SHAPES = [
    (r"\b(?:wanted|intended|hoped|meant) to\b", "INTENT"),
    (r"\bin order to\b", "INTENT"),
    (r"\bdecided(?: ,|,)? (?:early|late|that|to)\b", "INTENT"),
    (r"\bbecause (?:of )?(?:it|they|he|she|nobody|no one)\b", "CAUSAL"),
    (r"\bso that\b", "CAUSAL"),
    (r"\bwhich is why\b", "CAUSAL"),
]


def _sentences_of(text: str) -> list:
    body = text.split("---", 2)[2] if text.startswith("---") else text
    body = re.sub(r"^#\s+.*\n", "", body.strip(), count=1)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]


def negative_claim_scan(article_text: str) -> list:
    """Every sentence whose SHAPE asserts an absence, exclusivity or first/last."""
    out = []
    for s in _sentences_of(article_text):
        for pat, kind in NEGATIVE_SHAPES:
            if re.search(pat, s, re.I):
                out.append({"sentence": s, "kind": kind,
                            "pattern": pat.replace(r"\b", "")[:44]})
                break
    return out


def intent_causal_scan(article_text: str) -> list:
    out = []
    for s in _sentences_of(article_text):
        for pat, kind in INTENT_SHAPES:
            if re.search(pat, s, re.I):
                out.append({"sentence": s, "kind": kind})
                break
    return out


def negative_admission_audit(article_text: str, ledger: dict) -> dict:
    """A negative-shaped sentence needs a ledger fact of a negative type behind it.

    The pairing is reported, not inferred: each hit is matched against negative facts
    whose proposition shares substantial wording. Anything unmatched is a HOLD, and the
    prescribed repair is REMOVAL, never a caveat -- a caveat is how the research memo got
    into the prose in the first place.
    """
    from . import ledger as LG
    negs = {fid: f for fid, f in ledger.items()
            if f.get("claim_type") in LG.NEGATIVE_TYPES}
    hits = negative_claim_scan(article_text)
    unmatched = []
    for h in hits:
        sl = " ".join(h["sentence"].lower().split())
        ok = False
        for f in negs.values():
            key = [w for w in re.findall(r"[a-z]{5,}", f["proposition"].lower())
                   if w not in _FUNCTION_WORDS]
            if key and sum(1 for w in key if w in sl) >= max(2, len(key) // 3):
                ok = True
                break
        if not ok:
            unmatched.append(h)
    return {"negative_sentences": len(hits), "unmatched": unmatched,
            "ok": not unmatched,
            "negative_facts_available": sorted(negs)}


# ── FINAL LENS CONTRACT ───────────────────────────────────────────────────────
def validate_final_lens(final_lens: dict, arch: dict, ledger: dict) -> list:
    """The lens must change the meaning of material the reader already has.

    Independent readers said of the previous version: "the only paragraph with nobody in
    it", "a placeholder where a person should be", "fit is earned, not asserted". So the
    contract now names the beat BEFORE, the turn, and the beat AFTER, and requires the
    turn to say what the reader understands differently -- not where disability is
    mentioned.
    """
    errs = []
    need = ("lens_claim", "evidence_basis", "what_changes_for_the_reader",
            "story_beat_before", "crip_turn", "story_beat_after")
    for k in need:
        if not str(final_lens.get(k) or "").strip():
            errs.append("final lens missing %s" % k)
    if errs:
        return errs
    beat_ids = [b.get("beat_id") for b in (arch.get("beats") or [])]
    before, after = final_lens["story_beat_before"], final_lens["story_beat_after"]
    if before not in beat_ids:
        errs.append("story_beat_before %r is not a beat" % before)
    if after not in beat_ids:
        errs.append("story_beat_after %r is not a beat" % after)
    if before in beat_ids and after in beat_ids:
        if beat_ids.index(before) >= beat_ids.index(after):
            errs.append("the turn must sit between an earlier and a later beat "
                        "(%s then %s)" % (before, after))
    basis = set(final_lens.get("evidence_basis") or [])
    if isinstance(final_lens.get("evidence_basis"), str):
        basis = {final_lens["evidence_basis"]}
    unknown = basis - set(ledger)
    if unknown:
        errs.append("lens evidence_basis cites unknown facts: %s" % sorted(unknown))
    # the turn must re-read the BEFORE beat's carrier, not float
    tgt = [b for b in (arch.get("beats") or []) if b.get("beat_id") == before]
    if tgt:
        nouns = {w for w in re.findall(r"[a-z]{4,}",
                                       (tgt[0].get("concrete_carrier") or "").lower())
                 if w not in _FUNCTION_WORDS}
        if nouns and not any(n in final_lens["crip_turn"].lower() for n in nouns):
            errs.append("the crip turn names nothing from %s, the beat it re-reads" % before)
    if not re.search(r"\bunderstand|read|mean|see\b",
                     final_lens["what_changes_for_the_reader"], re.I):
        errs.append("what_changes_for_the_reader does not describe a change in "
                    "understanding")
    return errs
