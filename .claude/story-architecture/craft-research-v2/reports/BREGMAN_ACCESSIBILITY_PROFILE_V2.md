# Bregman / translator / editor public-prose profile v2

**Transferable craft, not style imitation.** This document exists to identify structural
and procedural moves that any writer could adopt. It is not a licence to reproduce a living
writer's voice or signature phrasing, and no phrase list, sentence template or vocabulary
dictionary derived from these texts should be built into the engine.

## 0. Sample and provenance

Fifteen public texts, 31,502 body words. One further candidate (`BR-16`) was retrieved but
turned out to be a navigation page and is recorded as UNAVAILABLE.

| provenance class | texts | lexical findings usable? |
|---|---|---|
| Substack, English, single-author newsletter (`BR-01`–`BR-07`) | 7 | Author's English is likely but unverified. `BR-01` is a book-manuscript excerpt. |
| Guardian, explicitly translated + edited (`BR-08`) | 1 | No. Translated by Elizabeth Manton and Erica Moore. |
| The Correspondent, explicitly translated + additionally edited (`BR-14`) | 1 | No. Translation Manton/Moore, additional editing Travis Mushett. |
| Guardian, translation status unconfirmed (`BR-09`–`BR-13`, `BR-15`) | 6 | Treat as unconfirmed. `BR-09` is credited to Erica Moore. |

So: **structural craft is analysable across all fifteen. Vocabulary and sentence-rhythm
findings are safe to attribute only to the seven Substack texts, and even there the author's
hand cannot be separated from an editor's.** Where a lexical claim appears below, the
provenance class is named.

Guardian standfirsts ("decks") were captured as body paragraph 1 by the extractor and have
been moved out of the body for all seven Guardian/Correspondent items. This matters: several
of the decks carry the question or thesis, and the body then opens differently. Reading them
as openings — which an earlier pass of this analysis did — misclassifies the openings.

## 1. Form variation

Six forms in fifteen texts. He does not have one architecture.

| form | n | mean sentence | questions/1k | 1-clause share |
|---|---|---|---|---|
| ARGUMENTATIVE_ESSAY | 4 | 15.1 | 3.7 | 0.571 |
| EXPLANATORY_FEATURE | 1 | 16.3 | 9.1 | 0.542 |
| NARRATIVE_HISTORY | 2 | 15.1 | 3.2 | 0.584 |
| POLEMIC | 3 | 14.8 | 3.4 | 0.614 |
| REPORTED_ESSAY | 2 | 14.2 | 5.1 | 0.599 |
| SHORT_FEATURE | 3 | 16.7 | 8.4 | 0.639 |

Read carefully: **sentence economy is form-invariant** (14.2–16.7 across every form) while
**question density varies threefold by form** (3.2 in narrative history, 9.1 in the
explanatory feature). Sentence economy is who he is. Question density is what the form needs.

## 2. Openings

Coded from the body, with decks excluded.

| text | form | opening type | first concrete referent |
|---|---|---|---|
| BR-01 | narrative history | DATED_EVENT + SCENE | sentence 1 |
| BR-02 | argumentative essay | DIRECT_ADDRESS → DATED_EVENT | sentence 3 |
| BR-03 | reported essay | INSTITUTIONAL_CONTEXT | sentence 1 |
| BR-04 | argumentative essay | QUESTION (reported from readers) | sentence 1 |
| BR-05 | short feature | AUTHOR_AS_GUIDE / confession | sentence 1 |
| BR-06 | short feature | DIRECT_ADDRESS + PEOPLE | sentence 1 |
| BR-07 | polemic | EVENT | sentence 1 |
| BR-08 | narrative history | CONCEPT (high abstraction) | sentence 5+ |
| BR-09 | reported essay | CONCEPT (high abstraction) | sentence 3 |
| BR-10 | polemic | NEWS_FINDING (a company's losses) | sentence 1 |
| BR-11 | argumentative essay | PERSON (Thatcher) — question is in the deck | sentence 1 |
| BR-12 | polemic | HISTORICAL_FACT (Keynes) | sentence 1 |
| BR-13 | argumentative essay | EXPLICIT_THESIS about the article itself | sentence 4+ |
| BR-14 | explanatory feature | DATED_EVENT + SCENE | sentence 1 |
| BR-15 | short feature | CONCEPT | sentence 2 |

Findings:

- **He is less scene-first than the professional narrative-nonfiction control group.** Roughly
  5 of 15 openings are a scene or dated event, against 10 of 12 in the control exemplars.
- **Three openings are frankly abstract**, including the two texts most likely to be cited as
  his best narrative work.
- **The deck does orientation work.** In `BR-11` the question *"Why do poor people make so
  many bad decisions?"* is the deck; the body opens on Thatcher. In `BR-12` the deck carries a
  three-clause thesis; the body opens on Keynes. Crip Minds has no deck. If we borrow the
  structure without the deck, orientation has to move into paragraph 1 or be sacrificed.
- **Concrete arrives fast even when sentence 1 is abstract.** In 12 of 15 texts a person,
  object, date or place appears by sentence 3. That is the defensible version of "open
  concrete": not *the first thing* but *early*.

## 3. Story carriers

`BR-01` is carried by one man over 68 paragraphs. `BR-14` is carried by two natural
experiments (a casino, an Indian sugarcane harvest) with a named researcher as guide. `BR-02`
is carried by a **graph** — the METR capability curve, explicitly set against Al Gore's CO₂
curve as its rhyme. `BR-13` is carried by a single word, *rentier*.

So the carrier can be a person, an event, a chart, or a concept. What is constant is that the
carrier is **singular and returned to**. `BR-02` returns to the Gore/METR pairing at 0%, 19%,
24% and 96%. `BR-14` opens on the Cherokee casino, leaves it at paragraph 13, and returns at
39 to close the loop before the argument's final turn.

## 4. Concrete ↔ abstract movement

The clearest passage is `BR-02` paragraphs 53–61, which exists to make one abstract claim —
that frontier models are a biosecurity risk — survivable:

```
53  SCENE      a microbiologist is hired to pressure-test a chatbot        LOW
54  EVENT      that night, the bot explains how to modify a pathogen       LOW
55  ACTION     he is shaken enough to go for a walk                        LOW
56  COUNTER    "but you can already google this" + "three data points"     MID
57  EVIDENCE   one: chatbot beats 94% of PhD virologists                   MID
58  EVENT      two: a physician arrested in India, ricin, chatbot logs      LOW
59  CONTEXT    three: Aum Shinrikyo, a Japanese cult, 1990s                 LOW→MID
60  SCENE      March 1995, Tokyo rush hour, five plastic bags of sarin      LOW
61  ARGUMENT   in 1995 they could not get Ebola; today they could order DNA MID→HIGH
```

Nine paragraphs at LOW and MID to earn one HIGH sentence. The abstraction is never asserted
before the concrete sequence; it is the sequence's conclusion.

The mirror move is in paragraphs 67–73, where an abstraction is grounded *after* it is named:
the "resource curse" is introduced, then explained through a mechanism story about taxation
and consent (*"Rulers have always needed money… And the only place to get it was from their
subjects"*), then extended by analogy to the "Intelligence Curse". Abstraction is always
either the payoff of concrete material or immediately given a mechanism the reader can follow.

## 5. Reader curiosity — the pivot paragraph

The finding this campaign did not expect. Across 15 texts, 8% of paragraphs are 15 words or
fewer (Scientias: 0%; control exemplars: 3%, n=2). Nineteen percent of them contain a question
mark. They sit at structural hinges, and they carry either the reader's next question or a
bare verdict.

From `BR-02`, with position in the article:

```
  7%  The deniers are us.
 31%  But isn't it all a bubble?
 34%  But you know what? None of this proves anything. Let me show you why.
 60%  And that brings us to the deepest risk of all. Power.
 71%  So. What do we do?
 74%  It is, I think, the wrong answer.
 77%  So what does work?
 78%  Three things, at minimum.
```

From `BR-14`:

```
  8%  But the question still remained: Which was the cause, and which the effect?
 23%  Genes can't be undone. Poverty can.
 25%  A world without poverty – it might be the oldest utopia around.
 35%  But is that all there is to it?
 40%  It's the context, stupid.
 69%  So how did they do in the experiment?
 77%  So what can be done?
 83%  Poverty is not a lack of character. It's a lack of cash
 94%  It's a lack of cash.
```

This is the mechanism of the "breathing room" the owner is asking for. It is not achieved by
writing longer or gentler explanation. It is achieved by **putting white space around one
short sentence at the moment the reader needs to catch up** — and by making that sentence
either the question the reader already has, or the verdict they have just earned.

Note the distinction between two devices that look alike:

- **Reader question** — curiosity. *"So how did they do in the experiment?"*
- **Reader objection** — resistance. *"But isn't it all a bubble?"* / *"Now, the obvious
  objection: of course an AI executive predicts explosive growth."* / *"Some skeptics, when
  they hear this, say: but you can already google this stuff."*

He answers both, and he answers them where they arise, not in a section at the end.

## 6. Explanation timing

`BR-14` is the reference case. The reader is given, in order: a concrete natural experiment
(0–10); the causal question as a 13-word paragraph (4); the nature/nurture context (5); the
findings (6–10); an interpretation (11); a verdict pivot (12); the objection sequence and the
harsh statistics (14–19); *only then* the expert who will explain it (20); a slogan pivot
(21); the concept built up from perception to consequence (22–26); an analogy — the overloaded
computer (27); **the technical term, coined, at paragraph 28 of 50**; the crucial distinction
(29); the number translated into IQ points (30).

The term arrives at 56% of the article. Everything a reader needs to *want* it has already
happened. Term-to-explanation distance is negative: the explanation is the ramp, and the term
is the label put on it afterwards.

## 7. People

Named people do three distinct jobs:

- **Historical actor.** Benjamin Lay, Jefferson, Voltaire, Samuel Johnson. They act.
- **Expert explainer who is also a character.** Eldar Shafir gets an ambition (*"He wants
  nothing less than to establish a whole new field of science"*), a laugh, and a blank look
  when challenged. He is not a quote dispenser.
- **Author as guide.** *"I was 18 years old in 2006, and I was furious."* / *"I've personally
  never written a line of code in my life."* / *"To be honest: it surprised me too."* The
  author's own changed mind is the recurring structural device: he was wrong, and the reader
  is invited to travel the same distance.

Quote load is low — quote-bearing paragraph share 0.25 against 0.48 for the control exemplars.
The two narrative-history pieces are the exception (0.53, 0.62); the argument essays are near
zero (`BR-04`: 0.0).

## 8. Numbers

Dominant handling, coded from all quantity-bearing sentences:

- **TRANSLATED_TO_SCALE** — *"20,000 cigarettes per minute; 10 million per eight-hour shift"*;
  *"Our effects correspond to between 13 and 14 IQ points… comparable to losing a night's
  sleep"*; a data centre *"nearly four times the size of Central Park"*.
- **CONNECTED_TO_PERSON** — *"Thomas Jefferson declared 'that all men are created equal' and
  yet owned six hundred slaves — four of them his own children."*
- **COMPARED / SEQUENCED IN TIME** — the METR ladder; *"Corporate lobbying in the EU is up 50%
  since 2020"*; *"Up 44-fold in 15 months. No company in any era…"*
- **NUMBER AS ARGUMENT** — *"The '95% failure rate' includes the 80% of companies that never
  piloted any AI in the first place."*
- **LEFT_UNEXPLAINED** — it happens: *"In the United States, the figure is 188.8%."*

Density is unremarkable (11.8 per 1,000 words, same as the control group). The move is
qualitative and it is not applied universally.

## 9. Research visibility

`BR-01` is the decisive case: 5,072 words of prose carrying **38 footnotes** — Rediker,
Hochschild, Lepore, Locke, Boswell, a Dutch 18th-century theological tract. The prose contains
almost no source machinery. The research is *entirely present in authority and entirely absent
from the sentence*. When a source is named in-line it is because the naming is itself
interesting (*"published by none other than Benjamin Franklin"*).

This is the answer to §26 of the brief. The apparatus goes somewhere the reader can reach and
does not have to look at.

## 10. Vocabulary — Substack texts only

`AUTHOR_ENGLISH_UNVERIFIED`, seven texts.

- **Nominalisation density is the same as prestige nonfiction** (20.3 vs 20.2 per 1,000 words).
  He is not avoiding abstract nouns.
- **Passive constructions are the lowest of the three samples** (4.9 vs 6.7 controls, 5.8
  Scientias).
- **Direct address is 2.6× the control group** (20.9 vs 8.0 per 1,000 words) — *you*, *we*,
  *us* as a structural habit, not an occasional flourish.
- Modal hedging is *higher* than the control group (10.3 vs 7.7), which cuts against a reading
  of him as merely assertive. He asserts the shape and hedges the specifics.

The answer to the brief's question — *what makes the language easy without making the idea
easy?* — is not the words. It is that the difficult noun is left intact and the machinery
around it is dismantled. See §11.

## 11. Syntax — the central mechanism

This is the most transferable finding in the profile, and it has numbers.

| measure | Bregman (n=15) | control exemplars (n=12) | Scientias (n=25) |
|---|---|---|---|
| mean sentence length (words) | **15.31** | 19.66 | 15.80 |
| sentence length SD | **8.29** | 10.15 | 6.70 |
| 25th / 75th / 90th percentile | 9 / 20 / 26 | 12 / 26 / 33 | 11 / 20 / 24 |
| sentences ≤10 words | **34%** | 20% | 26% |
| sentences ≥30 words | **6%** | 17% | 5% |
| clause boundaries per sentence | **1.58** | 1.90 | 1.77 |
| commas per sentence | **0.88** | 1.35 | 0.54 |
| single-clause sentences | **60%** | 44% | 48% |
| sentences ≤12 words AND single-clause | **36%** | 22% | 25% |
| nominalisations per 1,000 words | 20.3 | 20.2 | 11.5 |

Hypothesis H2 — complex noun inside simple syntax — is **confirmed**. Bregman's abstract-noun
density matches prestige narrative nonfiction while his clause load, comma load and long-tail
sentence share are all substantially lower. The idea stays hard. The sentence gets out of the
way.

## 12. Paragraph rhythm

Mean 58 words per paragraph, 3.85 sentences, standard deviation **25.1 words** — against
Scientias' 15.9. He varies paragraph size violently. Eleven percent of paragraphs are a single
sentence, rising to 37% in one short feature. Eight percent are 15 words or fewer; 11% are 100
words or more, in the same articles.

The rhythm is: long paragraph, long paragraph, four-word paragraph. That is the shape of the
"calm, book-like reading" the owner wants — not uniform paragraphs, but a wide range with
deliberate holes.

## 13. Transitions

He signposts openly and often: *"Let me show you why." "First, look at user growth." "Next,
let's look at revenue." "So let's look for an analogy." "Let me start with what we should not
do." "Three things, at minimum. One:… Two:… Three:…"*

The control exemplars do the opposite. Their annotators praise head-to-tail transitions in
which a word from the previous paragraph reappears in the next, and braiding so quiet it is
*"almost unnoticeable"*.

**This directly disproves H8 as a general rule.** Visible signposting is a genre convention of
the argumentative essay in a spoken register, and Bregman is its most successful current
practitioner. If Crip Minds publishes narrative features, the brief's deletion test holds. If
it publishes argument, it does not. The engine has no business enforcing one of these
universally.

## 14. Thesis

Recorded per text: `EARLY_EXPLICIT` in `BR-13` (announces the article itself in paragraph 1),
`REPEATED_THESIS` in `BR-02` (*"My point is not, absolutely not… My point is that…"*),
`DELAYED_EXPLICIT` in `BR-14` (83%, then repeated as the final line), `EMERGENT` in `BR-01`
(the argument is carried by the biography and stated only in the last three paragraphs).

There is no rule here. There is a placement decision that tracks form.

## 15. Endings

- `BR-01`: a Quaker motto, then the unmarked grave — RETURN_TO_PERSON + QUIET_STOP.
- `BR-02`: *"And dare to fight for a wildly better future."* — MORAL + CALL.
- `BR-14`: the thesis as a five-word paragraph, *"It's a lack of cash."* — THESIS, and it is a
  callback to a pivot paragraph 11% earlier.
- `BR-13`: *"theirs are the shoulders that carry us all"* — CONSEQUENCE + PERSON.
- `BR-12`: *"We can handle the good life, if only we take the time."* — CONDITIONAL FUTURE.

Applying McPhee's upstream test to `BR-02`: the article could plausibly end at paragraph 104
(*"Stop the denial. Stop pretending this is hype."*) rather than 106. It probably could not end
one paragraph earlier still. `BR-14` could not end earlier — the last five paragraphs are
argument the reader needs.

## 16. Author-reported workflow, and whether it matches the corpus

`AUTHOR_REPORTED` evidence in this sample is thin and comes from inside the texts rather than
from interviews, which is a real limitation. What is visible:

- He states he tests ideas before books: *"Here's the very first article I wrote for De
  Correspondent on universal basic income back in 2013"* — the essay precedes the chapter,
  which precedes the book, and the Guardian pieces are then excerpts back out of the books.
  `BR-01` is announced as *"a manuscript about the history of abolitionism"* in progress.
- He reports changing his own mind as a method: *"And you know what? I was wrong."*
- `BR-01`'s 38 footnotes and `BR-14`'s named meta-analyses evidence heavy secondary research.

**Does author-reported method match corpus-observed method?** On the two points we can check,
yes: the essay-before-book pipeline is visible in the publication record, and the claimed
research volume is visible in the footnote apparatus. We did not locate craft interviews in
this campaign, so the fuller comparison the brief asks for in §31 remains open.

## 17. What Crip Minds should borrow

Ranked by strength of evidence, and every item is structural or procedural.

1. **The pivot paragraph.** A short standalone paragraph at a hinge, carrying the reader's
   open question or the verdict just earned. This is the highest-value borrowable device and
   nothing in PR #62 can currently produce one deliberately.
2. **The low clause load with a wide length range.** 55–60% single-clause sentences, under 1.0
   commas per sentence, under 6% of sentences with four or more clause boundaries, and a
   sentence-length spread from 9 to 26 words at the quartiles. This is a measurable target for
   the owner's "semantic compression" complaint.
3. **Explanation after the reason to need it**, with the term labelled after the ramp rather
   than defined before it.
4. **Numbers converted** — to a person, a familiar unit, a time series, or a scale.
5. **The objection written as its own paragraph**, answered where it arises.
6. **Research present in authority, absent from the sentence** — footnotes or an apparatus the
   reader can reach and need not look at.
7. **Form chosen per article**, with the opening type, thesis placement and signposting level
   following from the form rather than from a house default.

## 18. What Crip Minds should not borrow

1. **His voice.** The interrogative second-person newsletter manner is a personal signature at
   5.6× the question density and 2.6× the direct-address density of comparable prose. Copying
   it would make Crip Minds sound like an imitation of a living writer, which is both an
   artistic failure and the thing §4 of the brief forbids.
2. **The author-as-guide confession.** *"I was wrong"* requires a continuous authorial persona
   with a public history of positions. Crip Minds' personas have a documented history of
   generating false first-person testimony from backstory (see `cripminds_persona_wound_
   fabrication_mechanism`). This device is a fabrication vector here in a way it is not for him.
3. **Universal signposting.** It belongs to the argument essay, not to everything.
4. **The deck doing the orientation work.** He has a standfirst; we do not. Borrowing his body
   openings without accounting for the deck loses the reader's orientation entirely.
5. **His vocabulary.** Six of fifteen texts pass through a translator and an editor. There is
   no defensible "Bregman word list" to extract, and building one would be style imitation
   rather than craft transfer.
