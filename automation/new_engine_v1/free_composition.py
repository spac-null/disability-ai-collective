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
    WORTH           runs, and still gates -- but only on its EDITORIAL refusals. Its lens
                    reaches nothing: no byte of it is shown to the Writer, and the three
                    checks that asked whether that lens could be PLANNED from are recorded
                    instead of blocking. See `plan_inputs_required`.
    ARCHITECTURE    NOT RUN. No plan is built on this path.
    CUT_TERMS       NOT RUN. It is derived from the architecture.
    WRITER          NEW. The free argumentative Writer. See write_article_free.
    CONTINUITY      SKIPPED -- a whole-article rewrite of the prose we are preserving.
    PROSE_FINISH    SKIPPED -- same reason.
    PACKAGE         runs, from the finished article. No plan context is given to it.
    SAFETY          runs, with THIS path's own licensing (see licensing_record).
    GROUNDING       runs, unchanged -- it never saw the architecture or the ledger anyway.
    FACT_CHECK      runs, unchanged.
    READER          runs, unchanged.

WHAT THE MISSING PLAN TOOK WITH IT, stated plainly rather than left to be discovered. The
architecture also carried `definition_evidence`, the architect's own prohibitions, the CUT
accounting and (on FAST_LANE) claim mapping. None of those exist here. What replaces them
is not a like-for-like substitute and is not claimed to be: the Writer is given the WHOLE
Ledger rather than a curated subset, so there is no cut list to enforce and no withheld
material to leak; and every factual claim in the finished prose is checked afterwards by
Safety against the whole-Ledger licensing record, by Grounding against the frozen sources,
and by the world-relative Fact Check. Definition glosses in particular lose their
architecture-declared adjudication and are judged by Grounding like any other sentence.

THE BRIDGE ASSERTS THIS CONTRACT'S OWN INTEGRITY PROPERTY. `architecture_valid` is
replaced, for this engine only, by `writer_plan_free`: proof on the actual prompt bytes
that no plan reached the Writer, which `writer_inputs_are_plan_free` computes before the
call is made and the run records as `plan_free`. A run that cannot prove it does not
publish. That is the single most important property of this module.

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

- open however the material earns, from the six this publication allows:
    anecdotal   one short true incident, the smaller the better
    descriptive a place, an object or a moment, shown
    quotation   open on what somebody said -- their claim, their terms, attributed
    dialogue    an exchange between people, reported
    contrast    two things set against each other
    summary     the sharp claim itself, stated plainly and early
  NOT a question, and NOT a statistic. The standard repertoire has eight; this
  publication's MANIFESTO rules out two of them in writing -- "the opening line is
  a concrete moment or a sharp claim, never a question, never statistics, never
  throat-clearing" -- and the manifesto is senior to general craft advice. Owner
  decision, 2026-10-03, taken against the eight after both were put to him.
  What matters is that the first paragraph lands the reader inside the story, not
  which of the six it uses;
- and it is PERSONAL. Not where convenient -- always. Somebody did this, somebody
  decided it, somebody lives with it; a system did not happen to itself. A first
  paragraph about a field, a period, a theory or a debate is an abstraction
  however exact its nouns, and a reader has nowhere to stand in it.
  THE EVIDENCE CANNOT EXCUSE YOU FROM THIS. What it can withhold is a NAME: you
  may not name anyone the material does not name. You can always write the people
  anyway -- the men who built the system, the student who is taught it as given,
  the player whose hand does not fit the notation. Unnamed is not impersonal.
  FIRST PERSON IS THIS PUBLICATION'S REGISTER. The manifesto says the writing is
  "long-form, first-person, expert" -- a critic thinking on the page. What is
  forbidden is a different thing: INVENTED TESTIMONY. No fictional human
  simulation, no invented anecdote, no lived experience written for anyone, no
  sentence of the form 'as a Deaf person, I know'. Think in the first person; do
  not testify in it. The people in your piece are the people in the evidence;
- never a summary, never a list. A paragraph that sets down what is known, item
  after item, is a catalogue even when every item is true and interesting. If a
  passage could be reordered without loss, it is a list and it has to be rewritten
  as something happening to somebody;
- early, and in a paragraph of its own, say what the whole piece is about and why it
  is worth a reader's time. Not a summary of what follows -- the reason it exists.
  Every craft source calls this the paragraph that justifies the story;
- then MOVE BETWEEN KINDS OF MATERIAL rather than blocking them: what the record
  shows, then what somebody said about it, then back. Research, then a human
  voice, then research. Three paragraphs of findings in a row is a catalogue
  whatever the findings are;
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

QUOTATION MARKS MEAN VERBATIM.

Put quotation marks around somebody's words ONLY when you were given those words
verbatim. Where you were not, report what was said and name who said it -- Ezgi called
it the scale most suitable for easy writing; her lawyer says the letter never arrived.
That is still a quotation lede, still a human voice, and it is true.

Where the source wrote in another language, quote it in translation and SAY it is a
translation -- 'in Ezgi's words, translated from the Turkish'. A reader of this
publication cannot use the Turkish alone. Translating and marking it is ordinary
practice; presenting a translation as the original is not.

A quotation you assemble from a paraphrase is a fabrication however faithful it feels,
and so is combining two separated clauses, presenting an ellipsis as a verified
sentence, or paraphrasing inside the marks. Marks around a title, a term being named or
a phrase the article is examining are a different thing and are unaffected.

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
Otherwise write the world, not the paperwork.

DO NOT LET A SENTENCE ANNOUNCE ITS OWN STRUCTURAL JOB. Sentences like "Here is where the
obvious reading goes wrong", "Now the harder test", "It is worth following that route
backwards", "So go back to the beginning", "Read that list again and notice what it is"
tell the reader what the article is doing instead of telling them about the world. Write
the thing, not a note about the thing. A turn that is real does not need to be announced:
put the surprising fact next to the one it overturns and the reader will feel the turn
without being told one is coming. One-sentence paragraphs are fine and normal."""


# ── tempo, and the standard this will be judged against ───────────────────────
# WHY THIS EXISTS, and it is the same reason as everything else added to this prompt
# today: the engine already knew all of it and the Writer was never told.
#
# THE READER STAGE JUDGES NINE NAMED DIMENSIONS. They are written in plain language in
# READER_SYSTEM -- MOMENTUM is "does each paragraph earn the next", BREATHING is "is
# concrete material given room, or is every sentence carrying fact plus interpretation
# plus atmosphere plus conclusion at once". Those are exactly the questions "is it
# boring" and "is it calm", answered in advance, and the Writer had never seen them. It
# was being marked by an instrument it did not know existed.
#
# AND DENSITY WAS MEASURED, NOT GUESSED. Over 142 published Crip Minds articles, in the
# engine's own counting functions:
#
#     proper names   3.5 per 100 words   (middle half 2.7-4.6)
#     numbers        0.7 per 100 words   (middle half 0.5-1.0)
#     sentence       17.6 words          (middle half 15.7-21.4)
#     paragraph      3.4 sentences       (middle half 2.3-4.2)
#     length         ~1,060 words median
#
# It predicts the owner's own reading. The article he pressed STRONG on eight times sits
# inside the published band on every measure (names 4.1, numbers 1.0). The one he pressed
# TOO_MUCH_AT_ONCE on six times carries 6.2 names per 100 words -- a third above the
# upper quartile. The one he was LOST in six times carries 2.7 numbers per 100 words,
# nearly triple it. A name and a number are each a thing the reader must hold.
#
# THESE ARE NOT TARGETS AND NOT A GATE. Nothing measures the draft against them and
# refuses it; `prose_density` records the numbers beside the article so the next
# conversation about "too dense" starts from a figure. An article with a good reason to
# sit outside the band is a good article.
TEMPO_AND_STANDARD = """=== HOW THIS PUBLICATION ACTUALLY READS ===
Measured across 142 published Crip Minds articles. This is what its own prose does.
It is not a target to hit and not a rule -- it is the shape a reader of this
publication is used to, and a reason to stop and look if you are far outside it.

  length                    about 1,060 words
  distinct proper names     3.5 per 100 words   (most articles 2.7 - 4.6)
  distinct numbers          0.7 per 100 words   (most articles 0.5 - 1.0)
  words per sentence        17.6                (most articles 15.7 - 21.4)
  sentences per paragraph   3.4                 (most articles 2.3 - 4.2)

A NAME AND A NUMBER ARE EACH A THING THE READER MUST HOLD. That is why these are
counted and nothing else is, and why they are counted DISTINCT: a name you return to
is one object, a fourth new name in a paragraph is a fourth object arriving at once,
however well the sentences are built. Reusing a name you have already introduced
costs the reader nothing.

ONE MENTAL OBJECT AT A TIME. Let the reader finish forming one thing before the next
arrives. This is about how quickly new things arrive, not about how long a sentence
is: a long calm sentence carrying one idea is easier than three short ones carrying
four. Where the material is technical, slow down further -- a reader who is lost at
the third paragraph does not recover at the ninth.

KEEP A TECHNICAL TERM WHEN IT IS THE PRECISE ONE, and explain it in ordinary words at
first use, in a sentence. Simplify the SYNTAX around a difficult idea rather than
replacing the idea's own name with a vaguer word.

MAKE THE POINT LAND. A reader should be able to tell early what they are being invited
to notice, and should reach the turn by the end -- through the material, never through
an announcement. If the reading would otherwise disappear, state it once, plainly.
Subtlety is not invisibility, and an unreadable point is not a subtle one.

THE LAST PARAGRAPH ADDS. Deepen, turn, land, or show a consequence. Never restate.

=== WHAT A READER WILL BE ASKED ABOUT THIS ARTICLE ===
These are the questions, in their own words, that an editor puts to the finished piece.
You are writing against them, so you may as well know them.

  OPENING              Does the FIRST PARAGRAPH land the reader inside the story -- by
                       its end do they know what this is about and why it is worth
                       their time? HOW it does that is yours, from the six this
                       publication allows -- anecdotal, descriptive, quotation,
                       dialogue, contrast, summary. NOT a question and NOT a
                       statistic: the manifesto rules those out. So is its LENGTH.
                       The strongest are PERSONAL:
                       somebody doing, saying or undergoing something, or a situation
                       a reader can stand inside. An opening that names only systems,
                       fields, periods or debates fails however concrete its nouns, and
                       so does throat-clearing -- generality before the subject.
  READABILITY          Does any sentence need rereading before its main claim is clear?
  ACCESSIBLE_READING   Are difficult ideas carried in easy syntax and ordinary words?
                       Is every technical term explained at first use, in a sentence,
                       in plain words?
  MOMENTUM             Does each paragraph earn the next? A paragraph that restates an
                       earlier one in different abstract vocabulary fails.
  BREATHING            Is concrete material given room, or is every sentence carrying
                       fact plus interpretation plus atmosphere plus conclusion at once?
  RESEARCH_LOAD        Does the piece read as written selectively from wide research,
                       or as everything the writer found? One fact read three ways is
                       one fact.
  ENDING               Does it stop when the point lands, or add a closing paragraph
                       because articles are expected to have one? Returning to the
                       person, scene or object the piece opened on is NOT padding --
                       it is the standard close for a feature, and it is owed when
                       the opening was an anecdote or a scene. What fails is a
                       paragraph that restates the argument, widens to the general,
                       or exists because the piece felt unfinished.

Write so these are true, not so they are answerable."""


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


def permitted_material_block(ledger: dict) -> str:
    """What a Reader repair on this path may draw on: the frozen Ledger, and nothing else.

    The planned path hands its repair `ST.render(packet)` -- the working subset
    Architecture prepared. This path has no packet, and the thing it licenses from is the
    whole frozen Ledger, exactly as the Writer was given it. Rendered the same way the
    Writer saw it, so a repair cannot be licensed by a wording the Writer never read.

    It is a ceiling, not an instruction. `apply_reader_repair` separately refuses any edit
    that introduces a number or a name its own paragraph does not already carry, so this
    text is what a repair may REPHRASE toward, never new material it may add.
    """
    facts = "\n".join("  %s  %s" % (fid, str((f or {}).get("proposition") or "").strip())
                      for fid, f in sorted((ledger or {}).items()))
    return ("THE FROZEN EVIDENCE -- %d propositions, the only facts that exist:\n%s"
            % (len(ledger or {}), facts))


def narrower_scope_block(pack: dict) -> str:
    """The narrower subject research named for the anchor, rendered as a constraint.

    WHAT WAS DISCONNECTED, and for how long. `scope()` asks of every anchor for "a narrower
    subject the anchor actually supports", stores it on the pack, and the sufficiency
    assessment turns a non-empty answer into the NARROW verdict: the material cleared the
    thresholds, and a narrower subject was named. An external read-only
    audit of 53d27df traced the field end to end. research.py writes it. Nothing reads it
    -- not the planned path, not the free path, not either Writer. `runner` reads the
    verdict only to separate HOLD from proceed, so NARROW has always proceeded exactly like
    ARTICLE and the narrowing was dropped at the stage boundary. This is the thirteenth
    instance of the same pattern found in two days: computed, persisted, never reached.

    THE COST, ON THE ONE RUN WHERE IT WAS MEASURED.
    production-20260930T085346Z-54ca6694 was narrowed to whether named Inuit contributors
    appear in the formal scientific and legal record or only in narrative acknowledgement.
    Its 1,427-word draft does not examine that question, and it held at Reader after nine
    model calls. The hold is not attributable to this omission alone, and no claim is made
    here that rendering the scope would have passed it.

    THIS IS A CONSTRAINT, NOT EVIDENCE. It licenses no fact and adds none: it says which of
    the already-licensed facts the article may be ABOUT. The broad subject is quoted beside
    it so the Writer can see what it is being narrowed from, rather than receiving a
    substitute subject with no account of where it came from -- the same reason
    `source_attribution_block` shows a text's identity instead of leaving it inferable.

    Rendered on a non-empty `narrower_subject` rather than on the verdict string. The two
    agree wherever composition can see them, because the only verdict that carries a
    narrower subject without being NARROW is HOLD, and HOLD never reaches a Writer.

    THE WORDING IS EXACT BECAUSE AN ADVERSARY CAUGHT IT NOT BEING. The first draft of this
    block told the Writer that research "read the anchor and found it carries a narrower
    subject", and recorded the verdict "for that reason". Both overstate. `scope_prompt`
    asks one model call, on the anchor text alone and before any source is fetched, for the
    subject AND the narrower subject together (research.py:864-882); `scope()` parses the
    reply without checking either against anything; and the verdict flip is mechanical on
    non-emptiness (research.py:1265-1267). So the narrower subject is a judgement, not a
    finding. It is rendered anyway, and as a constraint, because the BROAD subject comes
    from the very same reply and the Writer is already told to write about that -- the two
    are equally grounded, and preferring the broad one is a preference, not a safeguard.
    What changed is that the prompt now says where both came from. A prompt that
    misdescribes the provenance of its own content is this project's most expensive
    recurring defect.
    """
    narrower = " ".join(str((pack or {}).get("narrower_subject") or "").split())
    if not narrower:
        return ""
    verdict = " ".join(str(((pack or {}).get("sufficiency") or {})
                           .get("verdict") or "").split())
    broad = " ".join(str((pack or {}).get("subject") or "").split())
    head = ("THE SCOPE THIS ARTICLE MUST KEEP. When research scoped this anchor it named "
            "two subjects in one reading: the one above, and a narrower one it judged the "
            "anchor actually supports. Both are that reading's judgement of the anchor, "
            "made before any source was fetched")
    if verdict:
        head += (", and the narrower one is why the sufficiency verdict is %s"
                 % verdict[:40])
    L = [head + ". Write about the narrower subject:", "  " + narrower[:400]]
    if broad:
        L += ["", "  Narrowed from, for your orientation only: " + broad[:300]]
    L.append("  Facts that bear only on the broader subject are context. They are not what "
             "this article is about, and the article does not owe them a place.")
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
        # THE LENS ARRIVED WITH NO FRAMING AT ALL on this path -- a bare heading and the
        # owner's text. So the most personal material in the system reached the Writer as
        # background about a publisher, and the prose came out as a report about a
        # subject. The text itself says, in its own words, PUT THE READER IN A ROOM, THE
        # IMAGE MAKES THE ARGUMENT, and EXPERIENCE IS THE ARGUMENT, SCHOLARSHIP IS
        # EVIDENCE. Those are instructions about how to write and nothing ever said so.
        #
        # The split matters and is stated rather than left to inference: the EXPERIENCES
        # are not facts about any subject and may never be asserted about one; the METHOD
        # is how this publication writes.
        parts.append(
            "=== WHAT THIS PUBLICATION IS, AND HOW IT WRITES ===\n"
            "Written by the person this publication belongs to.\n\n"
            "THE EXPERIENCES BELOW ARE NOT EVIDENCE. None of them may be asserted about "
            "your subject, and none of them is a fact about it.\n\n"
            "THE METHOD BELOW IS YOURS, AND IT IS NOT OPTIONAL. An image, an object or a "
            "moment carries the argument; the reader arrives at the point before it is "
            "named; the citation comes after, if at all. A piece that explains its "
            "argument and then mentions an image has done this backwards.\n\n"
            + lens)
    corpus = CC.block()
    if corpus:
        parts.append(corpus)
    parts.append(READER_CONTRACT)
    # Directly after the reader contract, because it is its companion: the contract says
    # how to build the path through an idea, and this says how much of each fact to spend
    # on it. Before the one rule, which is the factual boundary everything else sits in.
    parts.append(COMPRESSION_AND_CARRY)
    # Tempo and the judging criteria sit with the other writing guidance, before the
    # factual boundary that everything else operates inside.
    parts.append(TEMPO_AND_STANDARD)
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

    THE SUBJECT CAN ARRIVE NARROWED. Research may find the anchor supports only a narrower
    subject than the run is named after. `narrower_scope_block` renders that finding
    directly under the subject it constrains, so the broad subject is never read without
    it.
    """
    q = instrument or {}
    L = []
    if subject:
        L += ["THE SUBJECT THIS RUN IS ABOUT:", "  " + subject, ""]
    # Directly under the subject it narrows, so the Writer never reads the broad subject
    # without its constraint. NOTE, because the rendered bytes say so and a comment
    # claiming otherwise would be the exact methodological error this module was written
    # to avoid: the EDITORIAL INTENT header inserted below goes to index 0 and has no
    # terminator, so this block IS rendered under it, as `source_attribution_block`
    # already is. Harmless here -- a scope constraint is not evidence and asserts no fact,
    # which is what that header says. Not harmless for the source block; see
    # .claude/free-path-disconnection-audit-2026-09-30.md, unfixed and deliberately not
    # bundled into this change.
    scope_block = narrower_scope_block(pack or {})
    if scope_block:
        L += [scope_block, ""]
    if q.get("question"):
        L += ["THE QUESTION THIS RUN IS FOR (written by the owner, before any evidence "
              "existed):", "  " + str(q["question"]), ""]
        # THE SECOND INSTRUCTION, WHICH USED TO BE MISSING. The EDITORIAL INTENT header
        # above is a licensing statement and nothing else: it says this question may not
        # be ASSERTED. Nothing ever said the article must ANSWER it. Nothing else in the
        # prompt did either -- READER_CONTRACT asks for an opening, momentum and an
        # ending, and the engine's one nut-graf-shaped field (`wants_next`, story.py) sits
        # inside `beats`, on the path this one replaced. So the sentence stating why the
        # piece exists reached the Writer under a prohibition and no purpose, while six of
        # the craft sources put saying-why-early ahead of everything else a piece does.
        #
        # IT LICENSES NOTHING, which is why it can sit under that header without
        # contradicting it. "Answer the question" is a statement about what the article is
        # for; every fact in the answer still comes from the frozen evidence below, and a
        # mechanism written as established is still an unlicensed claim Safety refuses.
        # Placed beside the question rather than after the whole block, so it is read with
        # the thing it refers to.
        L += ["WHAT THE ARTICLE OWES THAT QUESTION: answer it. Not assert it -- answer "
              "it, out of the frozen evidence below, and let the answer be whatever that "
              "evidence makes it: support, refusal, or something more complicated than "
              "either. A reader who reaches the end should know what was asked and what "
              "this evidence says about it.",
              # Both sentences below were added after an adversary measured what the
              # instruction above invites. Neither narrows the answer; both say how to
              # write it so the engine does not refuse a compliant one.
              #
              # ANSWERING IS NOT A LICENCE TO CONNECT. Measured: with the removal of
              # instruction and the practice of transmission both licensed and no source
              # relating them, "the conservatory removed it, ending transmission by mesk"
              # passes factual_surface_audit and safety_audit, leaving Grounding alone
              # against it. Two facts in one sentence with nothing licensed between them
              # is the project's oldest failure mode, and "answer the question" is exactly
              # the pressure that produces it.
              "  Answering does not license a connection. If two facts sit next to each "
              "other and no source relates them, they stay unrelated in the prose: do not "
              "make one the cause, the consequence or the end of the other.",
              # A REFUSAL MUST REST ON A LICENSED ABSENCE. Measured: "the record does not
              # show that X ended Y" passes the factual surface and then holds on
              # UNSUPPORTED_NEGATIVES, because the Ledger grants no such absence. Inviting
              # "refusal" as an answer without saying this invites a hold.
              "  And if the answer is that the evidence does not settle it, say that only "
              "where an absence is licensed -- the permitted absences are listed below. "
              "Otherwise show the limit by what the evidence DOES say, and stop there. An "
              "unlicensed 'the record does not show' is a new factual claim and will be "
              "refused.",
              "  Make the reason to read plain EARLY. Before a reader has spent much of "
              "their attention, the piece has to show why it is worth the rest of it -- "
              "not by summarising what follows, and not by opening on the question in the "
              "abstract, but by putting the concrete thing in front of them and making "
              "plain why it matters.", ""]
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
    L += ["", negative_permissions_block(ledger or {})]
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
    # DIRECTION IS PART OF THE LICENCE (2026-09-30, external audit). This rendered every
    # join as "A <-> B". A CAUSE is not symmetric: the freeze validated that the budget cut
    # caused the closure, and "<->" licenses the reverse just as strongly. The retained
    # free run that reached the Reader carried FOUR CAUSE relations in that format, so the
    # Writer was handed directional evidence with the direction stripped off and full
    # permission to assert it either way. Rendered as subject -> kind -> object now, and
    # the block says in as many words that the arrow is the licensed direction.
    L = ["LICENSED CONNECTIONS. These propositions are connected, and the connection "
         "itself is evidence you may assert. No other connection between two facts is "
         "licensed: placing two facts side by side is allowed, asserting that one causes, "
         "explains or follows from the other is not unless it is listed here.",
         "  THE ARROW IS THE LICENCE. Each line reads FROM -> TO, and only that "
         "direction is licensed. A cause is not reversible: if the arrow runs from A to "
         "B, you may not write that B brought about A."]
    for r in rels:
        if not isinstance(r, dict):
            continue
        subj = str((ledger.get(r.get("subject")) or {}).get("proposition") or "").strip()
        obj = str((ledger.get(r.get("object")) or {}).get("proposition") or "").strip()
        if subj and obj:
            L.append("  %s" % subj)
            L.append("     --%s-->  %s" % (str(r.get("kind") or "RELATED"), obj))
    return "\n".join(L) if len(L) > 1 else ""


# Published medians and middle half, from the same 142-article measurement the
# TEMPO_AND_STANDARD block quotes. Kept beside the measure so a reader of one finds the
# other, and so a future re-measurement changes both together.
PUBLISHED_PROSE = {
    "names_per_100w": (3.5, 2.7, 4.6),
    "numbers_per_100w": (0.7, 0.5, 1.0),
    "words_per_sentence": (17.6, 15.7, 21.4),
    "sentences_per_paragraph": (3.4, 2.3, 4.2),
}


def prose_density(article_text: str) -> dict:
    """What this draft's tempo actually is, beside what the publication's own prose does.

    TELEMETRY. It measures and records; it refuses nothing, and no stage reads it. The
    point is that "too dense" should arrive as a figure rather than as a button-press
    three hours later -- and on the three drafts so far it separates them correctly: the
    one the owner pressed STRONG on eight times sits inside the band on every measure, the
    one he found too much at once carries 6.2 names per 100 words against an upper
    quartile of 4.6, and the one he was lost in carries 2.7 numbers against 1.0.

    Names and numbers are counted DISTINCT, because `story._entities` and
    `story._numbers` return sets -- and that is the right unit here anyway: a name the
    reader meets a second time is not a second thing to hold. The published baseline was
    measured the same way, so the two are comparable.

    `writtenness` is a different and older measure, calibrated against 1,181 paragraphs of
    published nonfiction, and it was computed inside continuity_pass -- which this path
    does not run. So it is called here too rather than lost with the stage.
    """
    body = CP.CE.article_body(article_text or "")
    words = body.split()
    if not words:
        return {}
    n = len(words)
    sents = ST.split_sentences(body)
    paras = [x for x in CP.CE.paragraphs(body) if x.strip()]
    got = {
        "words": n,
        "names_per_100w": round(100.0 * len(
            ST._entities(body, skip_sentence_initial=True)) / n, 2),
        "numbers_per_100w": round(100.0 * len(ST._numbers(body)) / n, 2),
        "words_per_sentence": round(n / max(len(sents), 1), 2),
        "sentences_per_paragraph": round(len(sents) / max(len(paras), 1), 2),
        "paragraphs": len(paras),
    }
    outside = {}
    for k, (_med, lo, hi) in PUBLISHED_PROSE.items():
        v = got.get(k)
        if v is not None and not (lo <= v <= hi):
            outside[k] = {"draft": v, "published_middle_half": [lo, hi],
                          "direction": "above" if v > hi else "below"}
    got["published_middle_half"] = {k: [v[1], v[2]]
                                    for k, v in PUBLISHED_PROSE.items()}
    got["outside_published_range"] = outside
    try:
        got["writtenness"] = CP.CE.writtenness(article_text or "", None)
    except Exception:
        pass
    return got


def negative_permissions_block(ledger: dict) -> str:
    """The absences this Ledger can actually license, named. Ported from the planned path.

    WHY, measured three times. On both meŞk offline arms and again on
    rehearsal-20260930T173120Z-2cc116d7, Safety held on UNSUPPORTED_NEGATIVES. That last
    run makes the cause unmistakable: the Ledger held 57 facts and NOT ONE of them was
    negative-shaped, so no absence claim was licensable at all -- and the Writer declared
    eight, every one citing a positive fact. It was not ignoring the rule. It could not
    see which facts, if any, satisfied it.

    The planned path has never had this problem because `negative_permissions_block` shows
    its Writer the permitted negatives by id. The free path inherited the RULE and not the
    LIST. This is that list.

    AND FOR ITS FIRST DAY THE LIST WAS BUILT FROM THE WRONG POOL. It used
    `negative_shape_of` alone. That function is not a test of whether a proposition states
    an absence -- it is seventeen hand-written patterns for the shapes a WRITER reaches for
    when it over-claims one, and it matches none of these:

        The survey did not collect housing status.
        No records exist of the 1974 inspection.
        Lung function equations were not validated for this group.

    `negative_admission_audit`, the gate that enforces the rule, has never used it alone.
    Since 2026-09-20 its pool is facts the FREEZE TYPED negative -- ABSENCE,
    NEGATIVE_EXISTENCE, EXCLUSIVITY, FIRST_LAST, COMPARATIVE_NEGATION -- plus any other
    fact the shape matcher catches. So the permission list and the audit that enforces it
    were reading two different definitions of a negative, which is the one thing
    `negative_shape_of`'s own docstring says it exists to prevent.

    MEASURED ACROSS THE 120 RETAINED LEDGERS THAT HOLD ANY FACT. 505 facts are typed
    negative by the freeze; 128 are shape-matched; 85 are both. FOUR HUNDRED AND TWENTY
    LICENCES EXISTED THAT NO WRITER WAS EVER SHOWN. 93 of the 120 Ledgers hold at least
    one. THIRTY-SEVEN WERE TOLD "THE ABSENCES YOU MAY CLAIM: NONE" while holding typed
    negatives -- including rehearsal-20260930T173120Z, cited above as proof that the
    material had not arrived. It had: four typed absences in those 57 facts. And
    production-20260930T200948Z was shown 2 of its 13 before holding on
    PACKAGE_UNSUPPORTED_NEGATIVES.

    The pool is now exactly the audit's, so the two cannot disagree. This widens no
    permission Safety would refuse; it stops withholding the ones it already accepts.

    ATTRIBUTION CARRIES ITS CUE, because the audit says so. A fact admitted only by shape
    and typed ATTRIBUTION licenses an ATTRIBUTED sentence -- "the coroner said there is no
    known treatment" -- and prose that drops the cue and asserts the absence flatly is a
    different claim that still holds. Showing it without that condition would be a prompt
    promising a permission the gate will refuse.

    An empty Ledger of negations says so in as many words, because "write no sentence
    claiming an absence" is a far easier instruction to follow than "claim only absences
    some proposition carries" when none does.
    """
    facts = {fid: f for fid, f in sorted((ledger or {}).items()) if isinstance(f, dict)}
    typed = {fid for fid, f in facts.items()
             if f.get("claim_type") in LG.NEGATIVE_TYPES}
    shaped = {fid for fid, f in facts.items()
              if ST.negative_shape_of(str(f.get("proposition") or ""))[0]}
    negs = {fid: str(facts[fid].get("proposition") or "").strip()
            for fid in sorted(typed | shaped)}
    negs = {fid: prop for fid, prop in negs.items() if prop}
    if not negs:
        return ("THE ABSENCES YOU MAY CLAIM: NONE. No proposition above states that "
                "anything does not happen, does not exist, is absent, is unmeasured, is "
                "the only one or is the first. So do not write a sentence that claims "
                "one -- not about the subject, and not as an aside. If a thing's absence "
                "seems obvious to you, that is your inference and not this evidence.")
    L = ["THE ABSENCES YOU MAY CLAIM, and no others. These are the only propositions that "
         "state that something does not happen, does not exist, is absent, is unmeasured, "
         "is the only one or is the first:"]
    for fid, prop in negs.items():
        # Exactly the audit's condition: shape-only admission of an ATTRIBUTION fact
        # licenses the attributed form and not the flat assertion.
        cue = (fid not in typed
               and facts[fid].get("claim_type") == "ATTRIBUTION")
        # The verbs are named rather than described. An adversary pointed out that "say
        # who states it" reads as satisfied by "the coroner ARGUED there is no known
        # treatment" -- which names the speaker and is still refused, because `argued` is
        # not in the audit's cue list. A prompt that promises a permission the gate
        # refuses is the same defect as a prompt that misstates its own provenance.
        L.append("  %s  %s%s" % (fid, prop,
                                 "   [attribute it -- said, states, writes, reports, "
                                 "records, notes, describes, according to, testified, "
                                 "concluded or found. This licenses the attributed "
                                 "sentence, not the flat claim]" if cue else ""))
    L.append("  A sentence claiming any other absence has no permission here. There is no "
             "permission for silence: a thing not mentioned above is not thereby absent.")
    return "\n".join(L)


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


def _bears_on(fact: dict, sentence: str) -> bool:
    """Does this fact's negation actually concern THIS claim of absence?

    ADDED 2026-09-30 after an external audit reproduced the gap: "There is no elevator in
    the museum" was admitted on a fact reading "There is no wheelchair entrance at the
    museum". Both are negations, so the shape test passed, and nothing asked whether the
    second was about the first. Safety then returned PASS.

    That made a DECLARATION weaker than the lexical path it exists to supplement --
    exactly backwards. `story.negative_admission_audit` already requires a fact's
    proposition to share substantial wording with the sentence before it licenses one;
    a declaration was skipping that test entirely.

    So this applies the SAME rule, copied from that function rather than invented here:
    content words of five letters or more, function words dropped, and at least
    max(2, len(key) // 3) of them present in the sentence. A declaration can now only
    rescue a negative the lexical matcher missed for a mechanical reason -- never one it
    refused on substance.
    """
    key = [w for w in re.findall(r"[a-z]{5,}",
                                 str(fact.get("proposition") or "").lower())
           if w not in ST._FUNCTION_WORDS]
    if not key:
        return False
    sl = " ".join(str(sentence or "").lower().split())
    shared = sum(1 for w in key if w in sl)
    return shared >= max(2, len(key) // 3)


def counterevidence_left_out(ledger: dict, facts_used, instrument: dict | None) -> dict:
    """Frozen facts that bear on what would REFUTE the claim, and never reached the prose.

    THE ONE QUESTION NOTHING ASKED. Every check on this path asks whether what the article
    SAYS is supported -- Safety, Grounding, Fact Check, the claim mapper, the negative
    audit, all of them. Not one asks what the article LEFT OUT. So evidence that
    complicates the story can simply go unused, the piece passes every gate, and nobody
    knows. `disconfirming_shape` -- the owner's own statement, written before any evidence
    existed, of what would refute the claim -- is shown to the Writer under WHAT WOULD
    REFUTE IT and then never looked at again.

    That gap got more expensive on 2026-10-03, when the Writer began seeing the sources'
    verbatim sentences. A strong piece built around two striking quotes is exactly the
    piece most likely to walk past the awkward fact.

    IT IS TELEMETRY AND IT REFUSES NOTHING, deliberately -- the same standing as
    `prose_density`. "The Writer did not use F42" is not a safety violation, this cannot
    judge relevance reliably, and a gate built on a lexical overlap would refuse good
    articles for sport. It records, the owner reads, and he decides whether an omission
    mattered.

    RELEVANCE IS NOT INVENTED HERE. It reuses `_bears_on`, the test this module already
    trusts to decide whether a fact concerns a sentence -- content words of five letters
    or more, function words dropped, a third of them shared. Copied rather than invented
    is the rule that produced it in the first place.

    WHAT IT CANNOT DO. `facts_used` is the Writer's own declaration, so a run that emits
    no FACTS marker yields `no_declaration` rather than flagging all 77 facts as omitted:
    an absent declaration is missing information, not evidence of suppression.
    """
    refuted_if = str((instrument or {}).get("disconfirming_shape") or "").strip()
    if not refuted_if:
        return {"status": "no_disconfirming_shape", "candidates": [], "count": 0}
    declared = {f for f in (facts_used or []) if f in (ledger or {})}
    if not declared:
        return {"status": "no_declaration", "refuted_if": refuted_if,
                "candidates": [], "count": 0}
    out = []
    for fid, f in sorted((ledger or {}).items()):
        if fid in declared:
            continue
        if _bears_on(f or {}, refuted_if):
            out.append({"fact_id": fid,
                        "proposition": str((f or {}).get("proposition") or "").strip()})
    return {"status": "review" if out else "clean",
            "refuted_if": refuted_if,
            "unused_checked": len(ledger or {}) - len(declared),
            "candidates": out,
            "count": len(out)}


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
            # The two refusals are different facts about the world and must not be
            # reported as one: "you cited nothing negative" and "you cited a negation
            # about something else" send a reader to different places.
            # THE SAME POOL AS THE PERMISSION LIST AND THE AUDIT, for the same reason and
            # in the same commit: this is the third reader of "which facts carry a
            # negation" and it was the second one built on the shape matcher alone. Left
            # narrow, it would reject the declaration of a typed absence the Writer was
            # just given permission to use -- losing its NEGATIVE_LINEAGE while Safety
            # accepted the sentence. Three call sites, one definition.
            negs = [f for f in fids
                    if (ledger.get(f) or {}).get("claim_type") in LG.NEGATIVE_TYPES
                    or ST.negative_shape_of(
                        str((ledger.get(f) or {}).get("proposition") or ""))[0]]
            negatives = [f for f in negs if _bears_on(ledger.get(f) or {}, sent)]
            if not negs:
                why.append("no cited fact carries a negation; a positive fact cannot "
                           "license a claim of absence")
            elif not negatives:
                why.append("the cited negation is about something else: %s -- a negation "
                           "licenses only the absence it actually states"
                           % "; ".join(
                               str((ledger.get(f) or {}).get("proposition") or "")[:120]
                               for f in negs[:2]))
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
            if not isinstance(e, CP.ProviderError) and not CP._is_cli_transport_error(e):
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
                    # SELF-REPORTED, AND SAID SO (2026-09-30, external audit). This is
                    # the Writer's own ---FACTS USED--- list. Nothing checks that a listed
                    # fact appears in the prose, so it cannot establish coverage and must
                    # not be quoted as if it did. Ids the Ledger does not contain are
                    # dropped and recorded: a Writer citing F404 is a signal, not a count.
                    "facts_used_self_reported": [f for f in parsed["facts_used"]
                                                 if f in (ledger or {})],
                    "facts_used_not_in_ledger": [f for f in parsed["facts_used"]
                                                 if f not in (ledger or {})],
                    "facts_used_count_self_reported": len(
                        [f for f in parsed["facts_used"] if f in (ledger or {})]),
                    "facts_used_is_self_reported": True,
                    "facts_available": len(ledger or {}),
                    "prose_density": prose_density(article),
                    # Advisory, read by nothing, refuses nothing. See the docstring.
                    "counterevidence_left_out": counterevidence_left_out(
                        ledger, parsed["facts_used"], instrument),
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
        # `plan_inputs_required=False` because ARCHITECTURE does not run below. Worth's
        # editorial refusals are untouched -- no particular about this subject, no
        # editorial delta over existing coverage, an inconsistent lens, a lens citing
        # facts that do not exist. What stops blocking is the three checks that ask
        # whether Worth's OWN lens could be planned from: the story_candidate's shape, a
        # named carrier, and whether that carrier could carry an article. Nothing reads
        # any of the three on this path, and a run refused on them is refused on behalf
        # of a plan that will never be built from a lens the Writer will never see.
        # They are recorded on the result instead.
        w = record(CP.WORTH, CP.worth_gate(
            P, ledger, subject, CP.HYP.from_instrument(instrument or {}),
            conflict_sink=_conflict_sink(out_dir, subject),
            plan_inputs_required=False))
        if stop_after == CP.WORTH:
            return out(article=None, package_out=None)

        # ── ARCHITECTURE + CUT: NOT RUN (owner-directed, 2026-09-30) ────────────────
        # They ran here until now for ONE reason: the publication-safety bridge required
        # ARCHITECTURE to have passed, so a plan had to be built even though this path
        # discards it. That is a stage whose output nothing reads and whose failure can
        # still kill the run, and it killed 14 of 178 production compositions (7.9%) --
        # every one of them an article lost over a plan that would never have been used.
        #
        # CUT_TERMS goes with it: it is derived FROM the architecture, and its cut list
        # binds nothing here (see the module docstring on CUT_LEAKAGE).
        #
        # The bridge now asserts the thing that is actually true of this contract instead
        # -- that no plan reached the Writer, which the run proves on the prompt bytes and
        # records as `plan_free`. See publication_safety_bridge._evaluate_new_engine_v1.
        # That is a swap of one contract assertion for the other contract's equivalent,
        # not a relaxation: no factual gate moves, and Safety, Grounding, Fact Check and
        # Reader are untouched.
        #
        # WORTH IS NOT AFFECTED and still gates. Its lens now has no consumer, which is
        # the honest state of affairs -- the lens existed to be planned around. The half
        # of Worth worth keeping is the half that asks whether this evidence carries a
        # testable reading at all, and that half is unchanged.
        for s, why in ((CP.ARCHITECTURE, "no plan is built on this path; the Writer "
                                         "chooses its own structure"),
                       (CP.CUT_TERMS, "derived from the architecture, which is not run")):
            st[s] = {"status": CP.SKIPPED, "reason": why, "model_calls": 0, "repairs": 0}
            calls[s] = repairs[s] = 0

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
            # record() ASSIGNS calls[PACKAGE] from the payload, so a package
            # regenerated after a repair erased the first call from the books --
            # reproduced by the external audit as 8 reported against 9 made. The
            # accumulate-after-record pattern is the one every repair path on the planned
            # path already uses; this path needed it too.
            before = calls.get(CP.PACKAGE, 0)
            out_pkg = record(CP.PACKAGE, CP.editorial_package(
                P, text, None, None, refusals))
            calls[CP.PACKAGE] = before + out_pkg.get("model_calls", 0)
            return out_pkg.get("package")

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

        # ── ONE PACKAGE-ONLY SAFETY REPAIR, the planned path's Stage 9c ──────────────
        # NOT PORTED WHEN THIS LADDER WAS WRITTEN, and rehearsal-20260930T173120Z-2cc116d7
        # is what that cost. `_safety_locate_findings` refuses the whole attempt unless
        # EVERY blocking finding is a repairable category, and PACKAGE_UNSUPPORTED_NEGATIVES
        # is not in SAFETY_REPAIRABLE_PREFIXES -- so one bad line in the five-line package
        # made the ARTICLE repair ineligible too, and a 915-word article died with zero
        # repair calls spent. The package has its own repair for exactly this; it simply
        # was not wired here.
        if sa["status"] != CP.PASS:
            comp = CP.package_only_safety_completion(
                P, sa, final, pkg, ledger, licensing, final, audit_fn=audit)
            if comp["attempted"]:
                prep = comp["repair"]
                calls[CP.SAFETY] = calls.get(CP.SAFETY, 0) + prep.get("model_calls", 0)
                if prep["status"] == CP.PASS:
                    # The repaired package proceeds as-is -- never regenerated after this,
                    # so nothing model-generated can invalidate the recheck below.
                    pkg = prep["package"]
                    before = calls.get(CP.SAFETY, 0)
                    sa = record(CP.SAFETY, audit(final, pkg))
                    sa["after_package_safety_repair"] = True
                    CP._carry_package_completion(sa, prep)
                    calls[CP.SAFETY] = before + prep.get("model_calls", 0)
                    repairs[CP.SAFETY] = 1

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

        # ── READER, AND ONE BOUNDED EDITORIAL COMPLETION. ────────────────────────────
        # THIS PATH DECLINED THE COMPLETION LOOP UNTIL 2026-10-01, on the reasoning that
        # "converting Reader feedback into an automatic whole-article rewrite is exactly
        # what would destroy the prose this path exists to protect". That was true of the
        # stage as it stood when this engine was written, and it stopped being true on
        # 2026-09-09, for the same reason: `reader_completion_loop` was rebuilt as a batch
        # of LOCAL EDITS, each confined to one paragraph, each quoted verbatim, each
        # mechanically verified by `apply_reader_repair`, and every candidate judged by
        # THE SAME safety_audit, the SAME package generation and the SAME reader_gate this
        # run already enforces. The module's own words: a wider blast radius was "never
        # the fix a Reader hold needed, it was just the shape the first version happened
        # to have". The objection outlived the thing it objected to.
        #
        # WHAT A READER HOLD ACTUALLY LOOKED LIKE. production-20260930T212300Z-474783da,
        # the furthest anything has reached: five dimensions PASSED, including BREATHING
        # and CRIP_MINDS_FIT. The four that held were -- explain three words, name the
        # document the piece is about, delete a paragraph restating an earlier one. Those
        # are line edits, and this is the stage that makes line edits.
        #
        # NOTHING FACTUAL MOVES. A proposal is a PROPOSAL: it is refused whole, with the
        # package it regenerated, if Safety or Grounding finds anything new, and the
        # article that reached here factually clean stays exactly as it is. No rerun of
        # Worth, the Ledger or the Writer. The free path passes no packet -- Architecture
        # never ran -- so `apply_reader_repair` licenses each edit against nothing but its
        # own paragraph, which is STRICTER than the planned path, not looser: an edit may
        # not introduce a number or a name at all.
        if reader:
            rg = record(CP.READER, CP.reader_gate(P, final, sa.get("advisories")))
            if rg["status"] != CP.PASS:
                rc = CP.reader_completion_loop(
                    # `draft_text` is the Writer's own first article, which the
                    # loop uses for its semantic-delta comparison. On this path
                    # that is wr["article_text"] -- `final` may already carry a
                    # Safety or Grounding repair, and comparing a candidate
                    # against a repaired text would measure the repair, not the
                    # candidate.
                    P, final, pkg, rg, {}, ledger, wr["article_text"], pack, None,
                    source_text, source_sha,
                    audit_fn=audit, package_fn=make_package,
                    gate_fn=lambda t, adv: CP.reader_gate(P, t, adv),
                    permitted_text=permitted_material_block(ledger))
                before_repair = final
                if rc["reader_repairs_accepted"]:
                    # Article and package move together or not at all: the package is the
                    # one the accepted article's own Safety approved.
                    final, pkg = rc["article_text"], rc["package"]
                # RECORD FIRST, ACCUMULATE AFTER -- `record` replaces st[stage] and RESETS
                # calls[stage] and repairs[stage] from the payload it is given, so
                # anything added before it is discarded. The planned path calls this "the
                # same accumulate-after-record pattern used everywhere above"; writing it
                # the other way round cost this block its entire completion audit on the
                # first run of its own test.
                rg = record(CP.READER, rc["gate"])
                calls[CP.READER] = calls.get(CP.READER, 0) + rc["reader_model_calls"]
                calls[CP.SAFETY] = calls.get(CP.SAFETY, 0) + rc["safety_model_calls"]
                calls[CP.GROUNDING] = (calls.get(CP.GROUNDING, 0)
                                       + rc["grounding_model_calls"])
                st[CP.READER].update({
                    k: rc[k] for k in (
                        "reader_completion_iterations", "reader_repair_proposals",
                        "reader_repairs_accepted", "reader_repairs_rejected",
                        "reader_completion_history", "reader_initial_blocker_count",
                        "reader_final_blocker_count")})
                if rc["reader_repairs_accepted"]:
                    repairs[CP.READER] = 1
                    st[CP.READER]["reader_repair_byte_delta"] = repair_byte_delta(
                        before_repair, final)
                if rg["status"] != CP.PASS:
                    return out(CP.READER,
                               "reader HOLD on %s" % ", ".join(sorted(rg["held"])),
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
                "facts_used_count_self_reported":
                    wr.get("facts_used_count_self_reported"),
                "facts_used_self_reported": wr.get("facts_used_self_reported"),
                "facts_used_not_in_ledger": wr.get("facts_used_not_in_ledger"),
                "plan_free": wr.get("plan_free"),
                "prose_density": wr.get("prose_density"),
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
