"""free_composition.py -- the FREE ARGUMENTATIVE composition path.

WHY THIS EXISTS, AND WHAT WAS MEASURED

Production articles read like documentation: source summaries, lists of facts, clinically
correct prose with no argumentative movement. The engine's historical answer was more
control before the Writer -- more beats, roles, carrier rules, validators and gates. On
2026-09-29 that answer was falsified on the engine's OWN frozen evidence.

One frozen Ledger (the meŞk run, production-20260929T204704Z-0f0cd7b9, 77 facts):

    CONTROL  the existing pipeline      22 facts selected,  781 words,
                                        names/100w 9.1, numbers/100w 1.2
    FREE     same evidence, no plan     57 facts used,     ~1350 words,
                                        names/100w 8.8, numbers/100w 1.6

The free draft read substantially better, and it used MORE evidence, not less. So the
ceiling was never the material and never fact density: it was ARGUMENTATIVE MOVEMENT --
opening on a paradox, letting each answer raise the next question, allowing the evidence
to complicate the thesis, ending somewhere that changes the opening. A lens discovered
inside a pile can only describe the pile. A plan that decides every beat before the writer
thinks produces prose that reports the plan.

A second blind A/B on the same material added ONE variable, a READER CONTRACT, and the
owner's blind reading preferred it: a stronger opening puzzle, a clear reason to be reading
each detail NOW, difficult material followed by a sentence that says what changed, and
counterevidence that complicates the argument instead of sitting in a fairness paragraph.

THE DOCTRINE THIS PATH IMPLEMENTS

    FREEDOM IN REASONING AND ARGUMENT. STRICTNESS ON NEW FACTUAL STATE.

The Writer may interpret, compare, notice, ask, juxtapose, complicate its own thesis, and
decide its own structure, order, headings and length. It may NOT invent a scene, a line of
dialogue, testimony, a motive, a chronology, a source identity, an author name, a
publication genre, an institution, a number, a causal relation, or a claim of absence.
Interpretation is not invention, and this path deliberately does not treat it as such --
that distinction is Grounding's, and Grounding has demonstrated it can make it.

WHAT RUNS, AND WHAT DOES NOT

    LEDGER          runs, unchanged. It remains the ONLY origin of factual permission.
    WORTH           runs, unchanged. SHADOW-ONLY: no byte of it reaches the Writer.
    ARCHITECTURE    runs, unchanged. SHADOW-ONLY: no byte of it reaches the Writer.
    CUT_TERMS       runs, unchanged. SHADOW-ONLY: its cuts bind nothing on this path.
    WRITER          NEW. The free argumentative Writer. See write_article_free.
    CONTINUITY      SKIPPED -- a whole-article rewrite of the prose we are preserving.
    PROSE_FINISH    SKIPPED -- same reason.
    PACKAGE         runs, from the finished article. No plan context is given to it.
    SAFETY          runs, with THIS path's own licensing (see licensing_record).
    GROUNDING       runs, unchanged -- it never saw the architecture or the ledger anyway.
    FACT_CHECK      runs, unchanged.
    READER          runs, unchanged.

WHY THE PLANNING STAGES STILL RUN AT ALL. They are a gate, not a plan, on this path. The
publication-safety bridge requires LEDGER, WORTH and ARCHITECTURE to have passed before it
will stamp an article publication-eligible, and that requirement is not this change's to
relax. They run exactly as they do today and decide exactly what they decide today; what
changed is only that their output no longer reaches the prose. This is the single most
important property of this module, and `writer_inputs_are_plan_free` exists to prove it.

WHAT SAFETY IS GIVEN, AND WHY IT IS NOT A RELAXATION

`safety_audit` is the packet-compliance auditor. Three of its screens ask "did the Writer
stay inside the plan it was given", and on a path with no plan they need a true referent
or they report a category error. Measured on both offline arms with the meŞk plan they had
never seen: CUT_LEAKAGE on facts F19/F20 -- Ledger facts, licensed and true, that the
ARCHITECTURE had chosen to cut. Blocking an article for using a licensed fact the plan
excluded, after telling it to choose its own facts, is exactly the contradiction this path
exists to remove.

So Safety is given what is TRUE of this path:

    packet  = a licensing record over the WHOLE Ledger -- nothing was withheld
    arch    = {}  nothing was planned
    cut     = {}  nothing was cut, so nothing can leak

Nothing is disabled and no screen is removed. Measured on both offline arms: every
CUT_LEAKAGE finding disappears, no new finding appears, and UNSUPPORTED_NEGATIVES still
blocks -- which is correct, because a claim of absence IS new factual state.

REPAIR BUDGET: AT MOST ONE OF EACH, AND NEITHER MAY BROADEN.
One Safety repair and one Grounding repair, both the existing production mechanisms with
their existing eligibility rules, each spending exactly one model call. Then the required
checks run again on the EXACT repaired bytes. There is no loop, no second proposal and no
re-grounding of identical bytes to obtain a kinder sample: the Grounder is
non-deterministic, and asking it twice until it agrees is not a check.
"""
from __future__ import annotations

import re

from . import composition as CP
from . import contracts as C
from . import craft_corpus as CC
from . import editorial_lens as EL
from . import ledger as LG
from . import story as ST

# The engine name this path reports as. It is `composition.COMPOSITION_FREE_ARGUMENTATIVE`
# -- imported rather than restated so the two can never drift apart.
CP_FREE_ARGUMENTATIVE = CP.COMPOSITION_FREE_ARGUMENTATIVE

# The writing contract's own name, recorded on the result beside the planned path's
# NORMAL / SAFE_RECOMPOSE / FAST_LANE so a retained run says which contract wrote it.
COMPOSE_FREE = "FREE_ARGUMENTATIVE"

# ── the reader contract ───────────────────────────────────────────────────────
# NOT A PERSONA. The reader is a COGNITIVE STATE, not a demographic: no age, no city, no
# education level, no imagined biography. The arm-B probe text is kept close to verbatim
# because it is the text that was actually measured -- a rewrite would be a new variable.
#
# NOT A VALIDATOR, EITHER. Nothing below is compiled into a gate, scored, or checked. It
# is writing guidance, and the Reader stage judges the finished article on its own terms
# exactly as it does today.
READER_CONTRACT = """=== READER CONTRACT ===
Write for an intelligent general reader who knows nothing about this subject
and has not chosen to study it.

Your job is not to simplify the idea.
Your job is to make the path through the idea easy to follow.

The reader should never have to remember several unexplained concepts at once.

Build the article as a sequence of realizations:

- begin with one concrete anomaly, puzzle, person, object, action, or contradiction;
- let each answer create the next interesting question;
- introduce technical language only when the reader already needs it;
- explain one difficult idea at a time;
- prefer a concrete consequence over an abstract definition;
- use names only when the person matters to the developing argument;
- use numbers only when the number changes what the reader understands;
- do not summarize sources one after another;
- after difficult information, give the reader a short sentence that says
  what changed;
- allow the evidence to complicate the thesis;
- the ending should make something from the opening mean something different.

Do not lecture the reader.
Engineer discovery.

Do not imitate wording or distinctive phrases from the reference corpus.
Use it only to learn high-level craft: pacing, argument movement,
concretisation, explanation, surprise, and economy.

You decide the structure.
You may use any licensed Ledger proposition.
Do not invent new factual states."""


# ── how much of a fact to write ───────────────────────────────────────────────
# ADDED 2026-09-30, FROM THE FIRST READ OF A FREE-COMPOSITION ARTICLE. The owner read
# production-20260929T230317Z-36065d96 end to end and pressed STRONG eight times -- against
# one STRONG across the four articles read on 26-28 September -- and `I am lost`, `Why now?`
# and `Want more` did not occur at all. The orientation family is fixed.
#
# What he pressed instead was SOUNDS_LIKE_REPORT ten times, six of them LIST_OF_FACTS, and
# it was POSITIONAL: the opening block and the closing block were clean, and the collapse
# was the institutional middle. In his words:
#
#   "too much facts or written fully which doesnt need do that way all the time, writing
#    out literally whole names, numbers, those facts which could sometimes written
#    compactly. narrative should drive, not facts. wheelchair user who is subject in this
#    letter should have stronger place in narrative"
#
# THAT IS TWO FAULTS AND THE SECOND ONE IS NEW. Selection -- some facts did not earn their
# place -- was already addressed by "most of them will not earn their place". RENDERING was
# not addressed anywhere: a fact that DID earn its place was written out at full ceremony,
# because the Ledger stores each proposition in full and nothing told the Writer that a
# shorter form of a fact is still that fact.
#
# Measured on that article: the subject is named in paragraphs 2, 4, 11, 17, 18 and 22, and
# not once through 5-10 or 12-16. EVERY block that earned no STRONG is a block where the
# person is absent or vestigial.
#
# This is WRITING GUIDANCE. Nothing here is compiled into a validator, and no gate reads it.
COMPRESSION_AND_CARRY = """=== HOW MUCH OF A FACT TO WRITE ===
A fact that earns its place does not automatically earn its full form.

The Ledger records each fact completely, because that is what evidence has to do.
Prose does not. Write the shortest form that carries the sentence. A full registered
name, a statute number, a short title, an approval date, a chapter heading, a job
title, an institutional affiliation — these are usually the FORM a fact was recorded
in, not the thing the reader needs. "A law school clinic" is usually the right
rendering of a clinic's full registered name. "The bill" is usually the right
rendering of a bill's number, its short title, its approval date and the chapter it
sits in.

Compression is not omission and it is not vagueness. Be exact wherever exactness is
the point: a number that changes what the reader understands keeps every digit, and a
name the argument turns on is written out once, properly. The test is whether the
reader needs this much of it here.

A QUANTITY IS A FACT; ITS PRECISION USUALLY IS NOT. "Hundreds of supplier locations"
is the same fact as "more than 780 accredited Medicare and Medicaid supplier
locations", minus a precision the sentence was not using. Round it, unless the exact
figure is the thing the reader is meant to notice — a threshold, a comparison, a
change over time, or a number that is surprising at exactly that size. The same goes
for a date: "in 2022" is usually the fact, and "approved on June 2, 2022" is usually
the record it was taken from.

NARRATIVE DRIVES, NOT FACTS. If a paragraph exists because several facts were
available, it is a catalogue. Do not summarise sources one after another, and do not
walk through an organisation's position, then the next organisation's, then the next.

THE PERSON CARRIES THE WHOLE ARTICLE, NOT ONLY ITS ENDS. If this story has someone at
its centre, they belong in the middle of it too — inside the procedure, the
institutions and the documents, which is exactly where they are easiest to lose. A
long passage with no person and no concrete object in it is where a reader stops.

PROVENANCE IS NOT NARRATION. Say the supported thing instead of reporting that it is
supported: not "the source says", "the record establishes", "the available evidence
shows", "the reviewer noted". Name a speaker where the naming is part of the claim.
Otherwise write the world, not the paperwork."""


# ── the one rule ──────────────────────────────────────────────────────────────
# The probe's own control, kept because it IS the experiment: if the model may invent,
# a beautiful draft proves nothing about whether this material could carry one.
#
# The SOURCE IDENTITY paragraph is the one addition to the probe's wording, and it exists
# because of a measured, systematic defect rather than a worry -- see
# source_attribution_block.
ONE_RULE = """=== THE ONE RULE ===
Every factual statement must come from the numbered propositions you are given.
You may select, order, compress, withhold and interpret freely. You may place two
facts beside each other and let a reader draw a conclusion. You may NOT assert a
connection the propositions do not carry, and you may NOT add a fact, a name, a
number, a date or a quotation that is not in them.

SOURCE IDENTITY IS A FACT LIKE ANY OTHER. Who wrote something, what they are called,
what they do, and what kind of publication carried it are factual claims. Assert them
only from the propositions or from the SOURCES table, and use exactly the identity
given there. Do not complete a partial name, do not give someone a first name, a title,
a role or an affiliation the material does not state, and do not name the genre or venue
of a text -- column, newspaper, essay, blog, journal -- unless it is stated. Where the
material does not identify a text's author or genre, refer to the text itself.

ABSENCE IS A FACT TOO. A sentence saying that something does not happen, does not exist,
is not measured, is missing, is the only one or is the first is a factual claim, and it
needs a proposition that carries that negation. If no proposition does, do not write the
sentence -- an inference that something must be absent is not evidence that it is.

There is no length target and no structure to satisfy. Use as few of the
propositions as the article needs. Most of them will not earn their place, and the
default is to leave one out: a fact belongs in the article because the argument needs
it there, not because it is available and true. If you cannot say what a sentence
changes for the reader, cut the sentence — do not find it a home.

This is not an instruction to write a short article or to use few facts. A long
article every one of whose facts is load-bearing is exactly right. What is wrong is a
paragraph that exists because material was available.

OUTPUT, in this order and nothing else:
  the finished article as markdown -- one '# title' line, then the prose;
  a line '---FACTS USED---' followed by the proposition ids you used;
  a line '---NEGATIVE CLAIMS---' followed by one line per sentence asserting an
  absence, written as:  <the sentence exactly as you wrote it> :: F12
  Write '---NEGATIVE CLAIMS---' with nothing after it if there are none."""

FACTS_MARKER = "---FACTS USED---"
NEGATIVES_MARKER = "---NEGATIVE CLAIMS---"

# The Writer is given room to think. The probe used 12k and produced ~1350 words with its
# reasoning; the packet Writer's 8k was sized for a planned article of prescribed length.
FREE_WRITER_MAX_TOKENS = 12_000

# Same floor as the packet Writer, and for the same reason: this catches a reply that is
# not an article, never a reply that is a short one.
MIN_WORDS = CP.WRITER_MIN_WORDS


def source_attribution_block(pack: dict) -> str:
    """Who the sources actually are, stated deterministically from the frozen pack.

    THE DEFECT THIS ANSWERS IS SYSTEMATIC, not a one-off. Two independent free Writer
    calls on the meŞk evidence produced the same class of factual error, and the Grounder
    caught all of it:

      "Ayşe Başak Levendoğlu notes one difficulty"   the author is N. Oya Levendoğlu; the
                                                     first names were invented outright
      "Yalçın Çetinkaya writes that Arel was born"   an author attribution the material
                                                     does not carry
      "A newspaper column arguing against"           the genre and venue of the polemic
                                                     are nowhere established

    The cause is not carelessness and it is not the reader contract, which was present in
    only one of the two arms. It is that the Writer was asked to write about texts while
    being shown no authoritative record of what those texts ARE, so it reconstructed their
    identity from context -- sometimes correctly, sometimes not, and with no way to tell
    the difference from inside the prose.

    The pack already holds the answer. `publisher`, `title`, `role` and `url` are recorded
    by acquisition from the fetch itself, so this costs no call and invents nothing. A
    source whose title the fetch never established is shown as untitled rather than
    described, because a guess here is the exact failure being closed.

    This is EVIDENCE, not instruction: it tells the Writer who a text is, and the ONE RULE
    tells it not to go beyond that. There is deliberately no regex gate on source-role
    language -- that class of validator has already been falsified on this project, and a
    name the Writer may legitimately use is indistinguishable, lexically, from one it may
    not.
    """
    sources = [s for s in (pack.get("sources") or []) if isinstance(s, dict)]
    if not sources:
        return ""
    L = ["THE SOURCES THESE PROPOSITIONS CAME FROM. This is the only authority for what a",
         "text is, who wrote it and what kind of publication carried it. Where a field is",
         "not given here, the material does not establish it and you may not supply it."]
    for s in sources:
        sid = str(s.get("source_id") or "?")
        title = " ".join(str(s.get("title") or "").split())[:180]
        bits = ["  %s  %s" % (sid, title or "(no title established)")]
        if s.get("publisher"):
            bits.append("      publisher: %s" % str(s["publisher"])[:80])
        if s.get("role"):
            bits.append("      role: %s" % str(s["role"])[:40])
        if s.get("url"):
            bits.append("      url: %s" % str(s["url"])[:200])
        L.extend(bits)
    L.append("  No author is named here unless a proposition names one. If a text's author")
    L.append("  or genre is not established, write about the text, not about its author.")
    return "\n".join(L)


def free_writer_system() -> str:
    """The system prompt. Lens first, then craft corpus, then reader contract, then rule.

    THE ORDER IS THE PROBE'S AND IT MATTERS. What the publication is comes before how to
    write, because it is not a rule -- it says what the work is for. The craft corpus comes
    before the reader contract because the contract refers to it. The one rule comes last
    because it is the boundary everything else operates inside.

    A missing lens or a missing corpus yields an empty block rather than a remembered
    substitute, exactly as `editorial_lens.block()` already does.
    """
    parts = ["You are writing one article for Crip Minds. Below is what the publication "
             "is, written by the person it belongs to, and then the craft corpus its "
             "house style was derived from. Read both. The corpus is the model; imitate "
             "the WAY IT MOVES, never its subjects or its sentences."]
    lens = EL.load()
    if lens:
        parts.append("=== WHAT THIS PUBLICATION IS ===\n" + lens)
    corpus = CC.block()
    if corpus:
        parts.append(corpus)
    parts.append(READER_CONTRACT)
    # Directly after the reader contract, because it is its companion: the contract says
    # how to build the path through an idea, and this says how much of each fact to spend
    # on it. Before the one rule, which is the factual boundary everything else sits in.
    parts.append(COMPRESSION_AND_CARRY)
    parts.append(ONE_RULE)
    return "\n\n".join(parts)


def free_writer_user(instrument: dict | None, ledger: dict, pack: dict | None = None,
                     subject: str = "", relations=None) -> str:
    """The editorial intent and the whole frozen evidence universe.

    THE INSTRUMENT IS THE OWNER'S, AND IT IS NOT EVIDENCE. Each approved instrument
    carries a MECHANISM (the claim being tested), a DISCONFIRMING SHAPE (what would refute
    it), CARRIERS (what kind of concrete subject can carry the question) and a FALSE MOVE
    (the wrong version of the story, named in advance). All four were written by the owner
    before any evidence existed, all four are loaded by `knowledge_first`, and until this
    path none of them reached a Writer. They are editorial intent: they license no fact,
    and the block below says so.

    THE LEDGER ARRIVES WHOLE. The old Architecture selected ~22 of 77 facts and the Writer
    saw only those. The measurement that produced this module used all 77 and the article
    was better for it. Permission is not instruction: the Writer is told plainly that most
    propositions will not earn their place.
    """
    q = instrument or {}
    L = []
    if subject:
        L += ["THE SUBJECT THIS RUN IS ABOUT:", "  " + subject, ""]
    if q.get("question"):
        L += ["THE QUESTION THIS RUN IS FOR (written by the owner, before any evidence "
              "existed):", "  " + str(q["question"]), ""]
    if q.get("mechanism"):
        L += ["THE MECHANISM -- the claim being tested. It is NOT established; the "
              "evidence may support it, refuse it or complicate it, and all three are "
              "real outcomes:", "  " + str(q["mechanism"]), ""]
    if q.get("disconfirming_shape"):
        L += ["WHAT WOULD REFUTE IT:", "  " + str(q["disconfirming_shape"]), ""]
    if q.get("carriers"):
        L += ["WHAT CAN CARRY THIS QUESTION (the kinds of concrete subject that hold it):",
              "  " + str(q["carriers"]), ""]
    if q.get("false_move"):
        L += ["THE WRONG VERSION OF THIS STORY, named by the owner. Do not write this:",
              "  " + str(q["false_move"]), ""]
    if L:
        L.insert(0, "EDITORIAL INTENT. None of the following is evidence and none of it "
                    "may be asserted as a fact about this story. It says what the run is "
                    "for.")
        L.insert(1, "")
    block = source_attribution_block(pack or {})
    if block:
        L += [block, ""]
    facts = "\n".join("  %s  %s" % (fid, str((f or {}).get("proposition") or "").strip())
                      for fid, f in sorted((ledger or {}).items()))
    L += ["THE FROZEN EVIDENCE -- %d propositions, the only facts that exist:"
          % len(ledger or {}), facts]
    joins = relation_block(ledger or {}, relations)
    if joins:
        L += ["", joins]
    return "\n".join(L)


def relation_block(ledger: dict, relations=None) -> str:
    """The licensed joins, as propositions rather than ids.

    A join IS evidence -- it is the one thing that lets the Writer assert that two facts
    are connected without manufacturing the connection itself, which is the defect that
    survived four planning controls on 2026-09-29. Rendered as text for the same reason
    the packet renders them: a join the Writer cannot read is a join it cannot use.

    Empty when the freeze produced none, which is the pre-2026-09-29 behaviour and correct.
    """
    rels = relations or []
    if not rels:
        return ""
    L = ["LICENSED CONNECTIONS. These propositions are connected, and the connection "
         "itself is evidence you may assert. No other connection between two facts is "
         "licensed: placing two facts side by side is allowed, asserting that one causes, "
         "explains or follows from the other is not unless it is listed here."]
    for r in rels:
        if not isinstance(r, dict):
            continue
        subj = str((ledger.get(r.get("subject")) or {}).get("proposition") or "").strip()
        obj = str((ledger.get(r.get("object")) or {}).get("proposition") or "").strip()
        if subj and obj:
            L.append("  [%s]  %s  <->  %s" % (str(r.get("kind") or "RELATED"), subj, obj))
    return "\n".join(L) if len(L) > 1 else ""


def parse_free_reply(text: str) -> dict:
    """Split the reply into article, declared fact ids and declared negative claims.

    Tolerant on the markers and strict on the article: a reply whose markers are missing
    still yields an article (the whole reply), because the markers are bookkeeping and the
    prose is the product. A marker that appears inside the prose cannot break this -- the
    LAST occurrence wins, and the article is everything before it.
    """
    body = CP._clean_article(text or "")
    negatives, facts_used = [], []

    if NEGATIVES_MARKER in body:
        body, _, tail = body.rpartition(NEGATIVES_MARKER)
        for line in tail.splitlines():
            line = line.strip().lstrip("-").strip()
            if not line:
                continue
            sentence, sep, ids = line.rpartition("::")
            if not sep:
                continue
            fids = re.findall(r"\bF\d+\b", ids)
            sentence = sentence.strip().strip('"').strip()
            if sentence and fids:
                negatives.append({"sentence": sentence, "fact_ids": fids})
        body = body.strip()

    if FACTS_MARKER in body:
        body, _, tail = body.rpartition(FACTS_MARKER)
        facts_used = re.findall(r"\bF\d+\b", tail)
        body = body.strip()

    return {"article_text": body.strip(),
            "facts_used": sorted(set(facts_used)),
            "declared_negatives": negatives}


def verify_declared_negatives(article_text: str, declared: list, ledger: dict) -> tuple:
    """(lineage, rejected). A declaration is admitted only if the LEDGER backs it.

    THIS IS STRICTER THAN TAKING THE WRITER'S WORD, which is the whole point. Three
    independent conditions, all mechanical, none of them the Writer's own opinion:

      1. the declared sentence is really a sentence of the article;
      2. every cited id is a real fact in the frozen Ledger;
      3. at least one cited fact's PROPOSITION is itself negative-shaped, decided by
         `story.negative_shape_of` -- the same function that produced the finding being
         answered. A positive fact cannot license a claim of absence.

    A declaration failing any of them is REJECTED and recorded; it does not become a
    permission. So a Writer cannot talk its way past the negative gate, and the gate keeps
    exactly the authority it has on the planned path.
    """
    by_id = CP.label_sentences(article_text)
    norm = {sid: " ".join(txt.split()) for sid, txt in by_id.items()}
    lineage, rejected = {}, []
    for d in (declared or []):
        sent = " ".join(str(d.get("sentence") or "").split())
        fids = [f for f in (d.get("fact_ids") or []) if f in (ledger or {})]
        sid = next((k for k, v in norm.items() if v == sent), None)
        if sid is None:
            # Not an exact sentence of the article. Substring is allowed because a Writer
            # may quote its own clause rather than the whole sentence; anything looser
            # would let a declaration attach itself to prose it does not describe.
            sid = next((k for k, v in norm.items() if sent and sent in v), None)
        why = []
        if sid is None:
            why.append("the declared sentence is not in the article")
        if not fids:
            why.append("no cited id is a fact in this Ledger")
        else:
            # `negative_shape_of` returns a (kind, pattern) PAIR and returns (None, None)
            # for prose carrying no negation -- which is a TRUTHY tuple. Testing the
            # tuple itself admits every fact ever cited and silently turns this check
            # into a rubber stamp. The kind is the answer; the tuple is not.
            negatives = [f for f in fids
                         if ST.negative_shape_of(
                             str((ledger.get(f) or {}).get("proposition") or ""))[0]]
            if not negatives:
                why.append("no cited fact carries a negation; a positive fact cannot "
                           "license a claim of absence")
            else:
                fids = negatives
        if why:
            rejected.append({"sentence": sent[:160], "fact_ids": d.get("fact_ids") or [],
                             "why": why})
            continue
        lineage[sid] = sorted(set(fids))
    return lineage, rejected


def licensing_record(ledger: dict, relations=None) -> dict:
    """What this path licensed, in the shape `safety_audit` takes.

    IT IS NOT A WRITER PACKET AND IS NEVER SHOWN TO THE WRITER. It is built from an EMPTY
    architecture on purpose: no spine, no opening, no beats, no ending move, no
    prohibitions. Nothing was planned, so there is nothing for it to say, and it renders to
    a few hundred characters of empty scaffolding that licenses nothing by itself.

    The licensing on this path comes from the LEDGER, which `factual_surface_audit` and
    `safety_audit` both fold in whole -- proposition and support span for every fact. That
    is exactly right here: on this path every frozen fact IS licensed, because the Writer
    was given every frozen fact.

    Persisted as LICENSING_RECORD.json rather than WRITER_PACKET.json so no later audit can
    mistake it for a packet some Writer was handed.
    """
    return ST.build_packet({}, {}, LG.propositions(ledger or {}), None, relations or [])


# Fields whose presence in the Writer's prompt would mean a plan reached the prose. Used
# by `writer_inputs_are_plan_free` and asserted by the tests: source-code review is not
# enough, because the defect this guards against is a prompt assembled at runtime.
PLAN_LEAK_MARKERS = (
    "THE PATH, IN ORDER", "OPEN ON", "WHAT THE STORY IS", "beat", "BEAT",
    "ending_move", "ENDING", "not yet:", "carried by:", "story_spine",
    "what carries the reader on from here", "explain plainly, once, here",
    "write the first beat", "LOAD_BEARING", "SUPPORTING",
)


def writer_inputs_are_plan_free(system: str, user: str) -> list:
    """Failures that would mean Story Architecture reached this Writer. Empty means clean.

    WHY THIS IS A FUNCTION AND NOT A COMMENT. This project has already made exactly one
    methodological mistake of this kind: an A/B arm told the Writer "you decide the order"
    while the system prompt still told it to "write the first beat". Both statements were
    true of the source code and the experiment was worthless. So the check is on the BYTES
    that are about to be sent, it runs on every free composition, and the run HOLDs rather
    than writing an article whose contract is self-contradictory.

    `beat` is matched as a whole word only: the craft corpus is prose about writing and may
    legitimately discuss how a paragraph beats, and the lens may say anything the owner
    wrote. The markers that matter are the packet renderer's own headings, which nothing
    else produces.
    """
    errs = []
    for marker in PLAN_LEAK_MARKERS:
        pattern = (r"\b%s\b" % re.escape(marker) if marker.lower() == "beat"
                   else re.escape(marker))
        if re.search(pattern, user):
            errs.append("the Writer's user prompt carries the planning marker %r" % marker)
    # The system prompt is the lens, the corpus, the contract and the rule. The packet
    # renderer's headings must not be in it either, but the corpus is prose ABOUT writing,
    # so only the unambiguous machine-generated headings are checked there.
    for marker in ("THE PATH, IN ORDER", "not yet:", "carried by:",
                   "explain plainly, once, here", "write the first beat"):
        if marker in system:
            errs.append("the Writer's system prompt carries the planning marker %r"
                        % marker)
    return errs


def write_article_free(provider, ledger: dict, instrument: dict | None = None,
                       pack: dict | None = None, subject: str = "",
                       relations=None) -> dict:
    """STAGE: the free argumentative Writer. ONE call, one mechanical retry.

    The retry is mechanical only -- same prompt, no feedback, no instruction to do better
    -- exactly like `composition.write_article`. Nothing here regenerates for quality.
    """
    system = free_writer_system()
    user = free_writer_user(instrument, ledger, pack, subject, relations)

    leaks = writer_inputs_are_plan_free(system, user)
    if leaks:
        raise CP.CompositionHold(
            CP.WRITER, CP.WRITER_HOLD,
            ["the free Writer's own prompt carries Story Architecture material; refusing "
             "to write under a self-contradictory contract"] + leaks[:6])

    last = ""
    for attempt in (1, 2):
        try:
            comp = provider.complete(system=system, user=user,
                                     max_tokens=FREE_WRITER_MAX_TOKENS)
        except Exception as e:
            if CP._is_subscription_limit(e):
                raise CP.CompositionHold(
                    CP.WRITER, CP.CLAUDE_SUBSCRIPTION_LIMIT,
                    ["the Claude subscription cannot serve this call: %s" % str(e)[:300],
                     "stopping; no paid fallback was attempted"])
            if not isinstance(e, CP.ProviderError) and type(e).__name__ != "ClaudeCLIError":
                raise
            raise CP.CompositionHold(CP.WRITER, CP.WRITER_HOLD,
                                     ["provider unavailable: %s" % e])
        parsed = parse_free_reply(comp.text)
        article = parsed["article_text"]
        if len(article.split()) >= MIN_WORDS and article.lstrip().startswith("#"):
            lineage, rejected = verify_declared_negatives(
                article, parsed["declared_negatives"], ledger)
            return {"status": CP.PASS, "article_text": article,
                    "prompt": user, "prompt_sha256": C.sha256_text(user),
                    "system_sha256": C.sha256_text(system),
                    "system_prompt_chars": len(system),
                    "code_identity": CP.PV.code_identity(),
                    "provider": CP._identity(comp, attempt),
                    "model_calls": attempt, "repairs": 0,
                    "words": len(article.split()),
                    "facts_used": parsed["facts_used"],
                    "facts_used_count": len(parsed["facts_used"]),
                    "facts_available": len(ledger or {}),
                    "negative_lineage_declared": parsed["declared_negatives"],
                    "negative_lineage_verified": lineage,
                    "negative_lineage_rejected": rejected,
                    "plan_free": True}
        last = ("empty reply" if not article else
                "%d words, title line %s"
                % (len(article.split()),
                   "present" if article.lstrip().startswith("#") else "missing"))
    raise CP.CompositionHold(
        CP.WRITER, CP.WRITER_HOLD,
        ["the free Writer produced nothing usable after one mechanical retry (%s)" % last])


# ══════════════════════════════════════════════════════════════════════════════
# THE LADDER
# ══════════════════════════════════════════════════════════════════════════════
# Stage names are `composition`'s own, so `composition["stages"]` has the shape the
# publication-safety bridge, the commissioning desk and every existing consumer already
# read. CONTINUITY and PROSE_FINISH report SKIPPED: they are whole-article rewrites of the
# prose this path exists to preserve, and nothing downstream requires them.
FREE_STAGES = CP.STAGES


def run_free_argumentative_composition(
        provider, *, pack: dict, source_text: str, source_sha: str,
        subject: str = "", fact_check: bool = True, reader: bool = True,
        package: bool = True, stop_after: str = "", fact_check_fn=None,
        out_dir=None, instrument: dict | None = None) -> dict:
    """Approved research material in; a free argumentative article out, or a HOLD.

    Returns a result of exactly the shape `run_story_architecture_composition` returns.
    Every existing consumer -- the runner's WRITER_OUTPUT emission, the decision, the
    publication-safety bridge, publish_best, the desk -- therefore works unchanged.

    NO FALLBACK RECOMPOSITION. A second composition here would be a second free draft from
    the same Ledger with no new information, which is not a repair, it is a resample. One
    story, one composition, one HOLD or one article.
    """
    import time

    P = CP.composition_provider(provider)
    subject = subject or pack.get("subject") or ""
    st = {s: {"status": CP.NOT_RUN} for s in FREE_STAGES}
    calls: dict = {}
    repairs: dict = {}
    t0 = time.time()
    elapsed: dict = {}
    marks = {"_last": time.time()}

    def record(stage, payload):
        now = time.time()
        elapsed[stage] = round(now - marks["_last"], 1)
        marks["_last"] = now
        st[stage] = payload
        calls[stage] = payload.get("model_calls", 0)
        repairs[stage] = payload.get("repairs", 0)
        return payload

    def out(failure_stage=None, failure_reason=None, code=None, article=None,
            package_out=None):
        result = {
            "engine": CP_FREE_ARGUMENTATIVE,
            "status": CP.PASS if failure_stage is None else CP.HOLD,
            "stages": {s: st[s].get("status", CP.NOT_RUN) for s in FREE_STAGES},
            "detail": st,
            "failure_stage": failure_stage,
            "failure_reason": failure_reason,
            "reason_code": code,
            "article_text": article,
            "package": package_out,
            "package_status": (st.get(CP.PACKAGE) or {}).get("package_status", CP.NOT_RUN),
            "article_surface": CP.SURFACE_PROSE_FINISH,
            "article_sha256": C.sha256_text(article or ""),
            "bundle_sha256": C.sha256_text(CP.bundle_text(article or "", package_out)),
            "stopped_after": stop_after or "",
            "publication_ready": bool(failure_stage is None and package_out
                                      and not stop_after),
            "owner_review": bool(failure_stage is None and not package_out),
            "words": len((article or "").split()),
            "model_calls_by_stage": dict(calls),
            "model_calls_total": sum(calls.values()),
            "repairs_by_stage": {k: v for k, v in repairs.items() if v},
            "advisories": (st.get(CP.SAFETY) or {}).get("advisories") or [],
            "runtime_by_stage": dict(elapsed),
            "compose_mode": COMPOSE_FREE,
            "replay": False,
            "replayed_stages": [],
            "runtime_seconds": round(time.time() - t0, 1),
            "subject": subject,
            # One composition, by construction. Recorded so a consumer that asks about
            # attempts gets an answer rather than a missing key.
            "composition_attempts_count": 1,
            "fallback_recomposition_triggered": False,
            "fallback_recomposition_reason": "the free path composes once; a second free "
                                             "draft from the same Ledger is a resample, "
                                             "not a repair",
            "winning_attempt": "A",
        }
        if out_dir is not None:
            CP.persist(out_dir, result)
            _persist_free(out_dir, result)
        return result

    final = None
    pkg = None
    try:
        # ── LEDGER. Unchanged, and still the only origin of factual permission. ──────
        led = record(CP.LEDGER, CP.freeze_ledger(P, pack, subject))
        ledger = led["ledger"]
        relations = list(led.get("relations") or [])

        # ── WORTH. Unchanged and still a gate. SHADOW-ONLY for the prose. ────────────
        # The instrument reaches Worth here for the first time in production: on the
        # planned path `run_story_architecture_composition(instrument=...)` exists but no
        # caller supplies it, so `HYP.from_instrument` has always received {}. That gap is
        # NOT fixed on the planned path by this change -- one defect class per deploy --
        # and is recorded in the deploy note.
        w = record(CP.WORTH, CP.worth_gate(
            P, ledger, subject, CP.HYP.from_instrument(instrument or {}),
            conflict_sink=_conflict_sink(out_dir, subject)))
        if stop_after == CP.WORTH:
            return out(article=None, package_out=None)

        # ── ARCHITECTURE + CUT. Unchanged and still gates. SHADOW-ONLY for the prose. ─
        # They decide exactly what they decide today. What changed is that NO BYTE of
        # either reaches the Writer -- `writer_inputs_are_plan_free` proves it on the
        # actual prompt bytes before the call is made, and holds the run if it is false.
        a = record(CP.ARCHITECTURE, CP.architect(
            P, ledger, w, subject, visual_context=CP.load_visual_context(out_dir)))
        arch = a["architecture"]
        record(CP.CUT_TERMS, CP.derive_cut_watch_terms(arch, ledger))

        # ── WRITER. Free. ────────────────────────────────────────────────────────────
        wr = record(CP.WRITER, write_article_free(
            P, ledger, instrument=instrument, pack=pack, subject=subject,
            relations=relations))
        final = wr["article_text"]
        lineage = wr["negative_lineage_verified"]

        # The two rewriting stages this path exists to avoid. Recorded, so a run says so.
        for s, why in ((CP.CONTINUITY, "a whole-article rewrite of free prose"),
                       (CP.PROSE_FINISH, "a whole-article polish of free prose")):
            st[s] = {"status": CP.SKIPPED, "reason": why, "model_calls": 0, "repairs": 0}
            calls[s] = repairs[s] = 0

        licensing = licensing_record(ledger, relations)

        def make_package(text, refusals=None):
            if not package:
                st[CP.PACKAGE] = {"status": CP.SKIPPED, "package": None,
                                  "package_status": CP.SKIPPED, "model_calls": 0,
                                  "repairs": 0}
                calls[CP.PACKAGE] = repairs[CP.PACKAGE] = 0
                return None
            # NO PLAN CONTEXT. `editorial_package` takes an architecture and a worth
            # verdict only to build context lines; passing None gives it the finished
            # article and its own schema, which is what it should be titling from anyway.
            # `check_package` still validates every name, number and quotation against the
            # article, and the package is still read by Safety, Grounding and Fact Check
            # inside the same bundle.
            return record(CP.PACKAGE, CP.editorial_package(
                P, text, None, None, refusals)).get("package")

        def audit(text, pkg_, **kw):
            r = CP.safety_audit(text, text, licensing, {}, ledger, {}, None, lineage,
                                package=pkg_, **kw)
            r["negative_lineage_used"] = lineage
            r["audited_text_sha256"] = C.sha256_text(text or "")
            r["licensing"] = "FREE_PATH_WHOLE_LEDGER"
            return r

        pkg = make_package(final)
        sa = record(CP.SAFETY, audit(final, pkg))

        # ── ONE Safety repair. Existing mechanism, existing eligibility rule. ─────────
        if sa["status"] != CP.PASS:
            sfindings = CP.safety_repair_findings(sa, final, CP.package_prose(pkg),
                                                  draft_text=final)
            if sfindings:
                srep = CP.safety_repair(P, final, sfindings, ledger, licensing)
                calls[CP.SAFETY] = calls.get(CP.SAFETY, 0) + srep.get("model_calls", 0)
                if srep["status"] == CP.PASS:
                    final = srep["article_text"]
                    pkg = make_package(final)
                    sa = record(CP.SAFETY, audit(final, pkg, repair=srep))
                    sa["after_safety_repair"] = True
                    repairs[CP.SAFETY] = 1
                    calls[CP.SAFETY] = calls.get(CP.SAFETY, 0) + srep.get("model_calls", 0)

        if sa["status"] != CP.PASS:
            return out(CP.SAFETY, "; ".join(sa["blocking"])[:600], CP.SAFETY_HOLD,
                       final, pkg)

        # ── GROUNDING. Unchanged. It never saw the architecture or the ledger anyway. ─
        g = record(CP.GROUNDING, CP.ground_candidate(
            P, CP.bundle_text(final, pkg), source_text, source_sha, pack))

        # ── THE ONE SURGICAL FACTUAL REPAIR ──────────────────────────────────────────
        # Subtractive and claim-local: `grounding_repair` proposes edits on the exact
        # findings and `apply_local_grounding_repair` refuses any edit whose replacement
        # introduces a number, entity or relation its own cited facts do not already
        # carry. It may narrow or drop. It may not broaden, and it may not touch prose no
        # finding named.
        #
        # This is the pattern the offline probe established: six tiny attribution
        # replacements took a free draft from three fatal findings to PASS with no
        # structural change at all.
        #
        # ONE ROUND. Then the required checks run again on the EXACT repaired bytes, and
        # whatever they say is the answer. The Grounder is non-deterministic; re-grounding
        # identical bytes until it agrees is not a check, and there is no path back here.
        if g["status"] != CP.PASS and CP.repairable_findings(g.get("blocking")):
            grep = CP.grounding_repair(P, final, g["blocking"], ledger, licensing)
            calls[CP.GROUNDING] = calls.get(CP.GROUNDING, 0) + grep.get("model_calls", 0)
            if grep["status"] == CP.PASS:
                before = final
                final = grep["article_text"]
                repairs[CP.GROUNDING] = 1
                # Byte integrity: what the repair actually touched, recorded so the claim
                # "only the flagged spans moved" is checkable rather than asserted.
                grep["byte_delta"] = repair_byte_delta(before, final)
                # The package was written from the pre-repair prose. A factual repair
                # changes the article, so the package is rebuilt from the bytes that will
                # actually publish -- never a mixed-version bundle.
                pkg = make_package(final)
                sa = record(CP.SAFETY, audit(final, pkg, repair=grep))
                sa["after_grounding_repair"] = True
                if sa["status"] != CP.PASS:
                    return out(CP.SAFETY,
                               "the surgical factual repair did not survive the safety "
                               "stack: %s" % "; ".join(sa["blocking"])[:400],
                               CP.SAFETY_HOLD, final, pkg)
                g_calls = calls.get(CP.GROUNDING, 0)
                g = record(CP.GROUNDING, CP.ground_candidate(
                    P, CP.bundle_text(final, pkg), source_text, source_sha, pack))
                g["after_surgical_repair"] = True
                g["surgical_repair"] = {k: grep.get(k) for k in
                                        ("edits", "findings_answered", "rejected_edits",
                                         "findings_left_unanswered", "byte_delta")}
                calls[CP.GROUNDING] = g_calls + g.get("model_calls", 1)
                repairs[CP.GROUNDING] = 1

        if g["status"] != CP.PASS:
            return out(CP.GROUNDING,
                       "grounding status %r; %d blocking finding(s): %s"
                       % (g["grounding_status"], len(g["blocking"]),
                          [("%s %s" % (f.get("classification"),
                                       str(f.get("quote") or "")[:70]))
                           for f in g["blocking"]][:4]),
                       CP.GROUNDING_HOLD, final, pkg)

        # ── FACT CHECK. Unchanged. ───────────────────────────────────────────────────
        if fact_check:
            fc = record(CP.FACT_CHECK,
                        (fact_check_fn or CP.fact_check_unavailable)(
                            CP.bundle_text(final, pkg)))
            if fc.get("status") == CP.HOLD:
                bad = fc.get("blocking_contradictions") or []
                fc["surfaces"] = sorted({CP.surface_of(str(c), pkg) for c in bad})
                return out(CP.FACT_CHECK,
                           "blocking contradiction(s) on %s: %s"
                           % (", ".join(fc["surfaces"]) or CP.ARTICLE_SURFACE, bad[:4]),
                           CP.FACT_CHECK_HOLD, final, pkg)
        else:
            st[CP.FACT_CHECK] = {"status": CP.SKIPPED}

        # ── READER. Unchanged, and NOT turned into a rewrite loop. ───────────────────
        # A Reader HOLD on this path is a HOLD: the article goes to the desk for the owner
        # to read, which is what the desk is for. Converting Reader feedback into an
        # automatic whole-article rewrite is exactly what would destroy the prose this
        # path exists to protect.
        if reader:
            rg = record(CP.READER, CP.reader_gate(P, final, sa.get("advisories")))
            if rg["status"] != CP.PASS:
                return out(CP.READER, "reader HOLD on %s" % ", ".join(sorted(rg["held"])),
                           CP.READER_HOLD, final, pkg)
        else:
            st[CP.READER] = {"status": CP.SKIPPED}

        return out(article=final, package_out=pkg)

    except CP.CompositionHold as e:
        elapsed[e.stage] = round(time.time() - marks["_last"], 1)
        st[e.stage] = dict(e.payload, status=CP.HOLD, code=e.code, reasons=e.reasons)
        return out(e.stage, "; ".join(e.reasons)[:600], e.code,
                   final or st.get(CP.WRITER, {}).get("article_text"), pkg)


def repair_byte_delta(before: str, after: str) -> dict:
    """What the surgical repair actually changed, measured rather than asserted.

    Paragraph-level, because that is the unit a reader would notice moving. A repair that
    reports more changed paragraphs than it had findings has not been surgical, and the
    number is on the record either way.
    """
    import difflib
    b = [p for p in (before or "").split("\n\n")]
    a = [p for p in (after or "").split("\n\n")]
    sm = difflib.SequenceMatcher(None, b, a)
    changed = [(tag, i1, i2, j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes()
               if tag != "equal"]
    return {"paragraphs_before": len(b), "paragraphs_after": len(a),
            "paragraphs_changed": sum(max(i2 - i1, j2 - j1)
                                      for _t, i1, i2, j1, j2 in changed),
            "chars_before": len(before or ""), "chars_after": len(after or ""),
            "similarity": round(difflib.SequenceMatcher(None, before or "",
                                                        after or "").ratio(), 4)}


def _persist_free(out_dir, result: dict) -> None:
    """The artifacts this path has that the planned path does not.

    `composition.persist` already wrote everything the two share. This adds the free
    Writer's own identity and the licensing record, under names that cannot be mistaken
    for a packet the Writer was handed. Never allowed to break a decided run.
    """
    import json
    import pathlib
    try:
        d = pathlib.Path(out_dir)
        d.mkdir(parents=True, exist_ok=True)
        det = result.get("detail") or {}
        wr = det.get(CP.WRITER) or {}
        if wr.get("prompt"):
            (d / "FREE_WRITER_PROMPT.txt").write_text(wr["prompt"], encoding="utf-8")
        if wr.get("prompt_sha256"):
            (d / "FREE_WRITER_CALL_IDENTITY.json").write_text(json.dumps({
                "code": wr.get("code_identity"),
                "compose_mode": COMPOSE_FREE,
                "system_sha256": wr.get("system_sha256"),
                "system_prompt_chars": wr.get("system_prompt_chars"),
                "prompt_sha256": wr.get("prompt_sha256"),
                "article_sha256": C.sha256_text(wr.get("article_text") or ""),
                "facts_available": wr.get("facts_available"),
                "facts_used_count": wr.get("facts_used_count"),
                "facts_used": wr.get("facts_used"),
                "plan_free": wr.get("plan_free"),
                "negative_lineage_verified": wr.get("negative_lineage_verified"),
                "negative_lineage_rejected": wr.get("negative_lineage_rejected"),
            }, indent=1, sort_keys=True, default=str), encoding="utf-8")
    except Exception:
        pass


# ── WHERE AN INSTRUMENT CONFLICT GOES SO THE OWNER CAN ACTUALLY FIND IT ───────
# Two places, on purpose. The run directory gets the full record beside the evidence that
# produced it, and one append-only file gathers every conflict across all runs, because
# the question the owner is actually asking -- "is this instrument repeatedly commissioning
# subjects Worth refuses, and should its rules be sharpened?" -- cannot be answered from
# inside a single run directory.
#
# Nothing reads either file back. They are for a person.
CONFLICT_LOG_DIR = "/srv/data/cripminds-instrument-conflicts"
CONFLICT_LOG = "CONFLICTS.jsonl"


def _conflict_sink(out_dir, subject: str):
    """A callable that files one instrument conflict. Never raises into a run."""
    def sink(record: dict) -> None:
        import datetime
        import json
        import pathlib
        row = dict(record, subject=record.get("subject") or subject,
                   at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   run=str(out_dir or "").rstrip("/").rsplit("/", 1)[-1])
        blob = json.dumps(row, indent=1, sort_keys=True, ensure_ascii=False,
                          default=str)
        if out_dir is not None:
            try:
                d = pathlib.Path(out_dir)
                d.mkdir(parents=True, exist_ok=True)
                (d / "INSTRUMENT_CONFLICT.json").write_text(blob, encoding="utf-8")
            except Exception:
                pass
        try:
            agg = pathlib.Path(CONFLICT_LOG_DIR)
            agg.mkdir(parents=True, exist_ok=True)
            with (agg / CONFLICT_LOG).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False,
                                    default=str) + "\n")
        except Exception:
            pass
    return sink
