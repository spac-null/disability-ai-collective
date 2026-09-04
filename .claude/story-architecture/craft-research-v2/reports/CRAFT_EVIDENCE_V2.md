# Craft evidence v2

What excellent accessible nonfiction actually does, established from published texts and
professional teaching material rather than from this project's prior assumptions.

Campaign date: 2026-09-04. No implementation code was read until the craft work was
finished, and no implementation code was changed.

**Revised 2026-09-04 after V1 seed artifacts were supplied.** Nine findings changed or were
added; one — D3/F-13 on transitions — was materially revised against a source the V1 pass had
and this pass had missed. Every change is cited to an original this pass fetched and read, not
to V1's paraphrase. Adjudication of all 48 V1 claims: `V1_V2_COMPARISON.md`. Sample sizes
grew to 18 Bregman texts (43,115 words) and 31 Scientias articles (19,829 words); no headline
number moved materially.

## 0. Reading order

1. This file — what we believed, what survived, what did not.
2. `CRAFT_METRICS_V2.md` — the numbers, with denominators.
3. `BREGMAN_ACCESSIBILITY_PROFILE_V2.md` — the owner's primary craft model, separated
   into transferable craft and personal habit.
4. `SCIENTIAS_EXPLANATION_PROFILE_V2.md` — how complex science is made legible.
5. `NONFICTION_REVERSE_ENGINEERING_V2.md` — paragraph-level maps.
6. `CRAFT_EXERCISES_V2.md` — professional exercises, and which stage could learn from each.
7. `PR62_CRAFT_GAP_ANALYSIS.md` — read-only comparison.

## 1. The six categories, kept apart

The brief requires these never be collapsed. Every finding below is tagged.

| tag | meaning |
|---|---|
| `CRAFT_TEACHING` | what journalism/nonfiction teachers say writers should do |
| `CORPUS_PATTERN` | what strong published texts measurably do |
| `AUTHOR_REPORTED` | what a writer says about their own method |
| `BREGMAN_SPECIFIC` | present in Bregman, absent or rare in the control group |
| `OWNER_PREFERENCE` | Crip Minds owner taste, not a law of journalism |
| `PROJECT_SAFETY` | a Crip Minds factual constraint, not a craft claim |

## 2. What we believed before

Reconstructed from `.claude/CLAUDE.md`, the memory notes, `STORY_ARCHITECTURE_MIGRATION_MAP.md`,
and the twelve hypotheses in the campaign brief. Stated plainly so it can be scored.

1. Good nonfiction opens on something concrete; an abstract opening is a defect.
2. Announcing a thesis is a defect; the idea should emerge.
3. Visible signpost transitions ("Now consider…") indicate constructed prose.
4. Short sentences are the mechanism of accessibility.
5. One-sentence paragraphs are performance slots and therefore a defect.
6. Every article needs a protagonist and a narrative spine.
7. Provenance language in reader prose is a defect.
8. Endings should be found by writing a better final move.
9. Semantic compression — fact + context + interpretation + atmosphere in one sentence — is
   a Crip Minds failure mode.
10. A reader-question model may order information better than fixed beats.

## 3. What the research confirmed

**C1. Information order should follow the reader's open question, not a fixed beat list.**
`CRAFT_TEACHING` + `CORPUS_PATTERN` + `BREGMAN_SPECIFIC`. This is the strongest result in
the campaign, and it arrived independently from four directions.

- Jacqui Banaszynski (Knight Chair in Editing, Missouri) on background: *"The background
  should answer, in brief, the questions that the reader has when the writer introduces
  something new or challenging or interesting. Answer questions like 'I don't get it', 'I
  don't know where this came from'… right then with a phrase, a sentence, maybe a short
  paragraph. But don't give all the background at once."* (TON, *Writing Elegant Background*)
- The Storygram annotator on Ed Yong's rhetorical question: it works *"because it sets up
  the crux of the problem … and is positioned in the exact place where readers might be
  asking themselves that same question."*
- Same annotator on Yong's history paragraph: it works because it is *"answering the
  questions readers are probably asking at this point: Why aren't there more right whales?"*
- Bregman implements it as visible text. In `BR-14` six paragraphs of 4–13 words each are
  a reader question or a verdict, placed at 8%, 23%, 25%, 35%, 40%, 69%, 77%, 83%, 90% and
  94% of the article. Two examples: *"But the question still remained: Which was the cause,
  and which the effect?"* and *"But is that all there is to it?"*

Hypothesis H12 is **confirmed**, and confirmed by teachers, by annotators of texts Bregman
had nothing to do with, and by Bregman.

**C2. Explanation lands after the reader has a reason to need it.** `CRAFT_TEACHING` +
`CORPUS_PATTERN`. H3 confirmed. Konnikova's annotator: *"She gives us a concrete example of
the scientific field being put to use before even trying to explain what the scientific
field is. This is an effective way of getting the reader invested."* Sokol's annotator on a
mid-article mercury explainer: *"The reader can pause here, understanding the threat … and
is invested enough to keep reading to find out why."* In `BR-14` the coined term *"mental
bandwidth"* arrives at paragraph 28 of 50 — after the overloaded-computer analogy at 27, and
after the reader has been given the question at 19. The explanation precedes the term; the
term–explanation distance is negative.

**C3. Concrete and abstract registers alternate, and the movement is a pacing instrument.**
`CRAFT_TEACHING` + `CORPUS_PATTERN`. H1 confirmed with an important addition. The ladder of
abstraction is taught not as decoration but as a remedy for stall: *"If a story feels stuck
or slow-paced, it might be a sign that it's time to switch to a different level of
abstraction"* (Lauren Gravitz, TON). Roy Peter Clark: *"There comes a point where you've told
the story, where you've described the detail, but you have to strive for meaning."* One apex
per story, chosen early, and the ladder should be bidirectional — the reader should be able
to carry the meaning back down into their own life.

**C4. Reporting for story material precedes writing.** `CRAFT_TEACHING` + `AUTHOR_REPORTED`.
H4 confirmed. TON's *How to Cultivate Narrative*: *"In the reporting stages, you'll need to
collect as many potential narrative kernels as possible."* Method sections are mined for
action; sources are asked the same question repeatedly; researchers are asked what colour,
how heavy, how it felt. The narrative material is **acquired**, not composed. This is the
single most consequential finding for Crip Minds safety, and section 8 below states why.

**C5. Strong texts vary article form.** `CORPUS_PATTERN`. H5 confirmed. The Bregman sample
alone spans narrative history, explanatory feature, reported essay, argumentative essay,
short feature and polemic — and the structural choices track form, not author (§5 of the
Bregman profile). Teaching names two incompatible background architectures (the WSJ model:
scene → nut graf → standalone background block → chronology; and the braided/layer-cake/zipper
model) and says the choice *"should depend on the publication's style, the material
available from reporting, and the nature of the story."* Rowińska reorganised a Quanta piece
away from chronology to a difference-based structure once the debate had more than two camps.

**C6. Concrete facts are allowed to stand before they are interpreted.** `CORPUS_PATTERN`.
H7 confirmed. `BR-14` reports the casino findings across paragraphs 6–10 and only interprets
at 11. Yong's whale-injury catalogue is praised for *"just the right amount of brutal
reality. Not skimming over the details, but not diving too deeply into them"* — description
without a moral attached to each item.

**C7. Semantic compression is real, measurable, and something strong texts largely avoid.**
`CORPUS_PATTERN`. H10 confirmed and given numbers. Across 15 Bregman texts, 60% of sentences
carry a single clause boundary, 4% carry four or more, and there are 0.88 commas per
sentence. The control exemplars are markedly denser (44% / 8% / 1.35) and Scientias is
denser still on clauses but lighter on commas (48% / 5% / 0.54). Bregman's METR passage is
the pattern in its purest form: *"In 2022, the answer was about 30 seconds. In 2023, it was
4 minutes. In 2024, it was 40 minutes. In 2025: 6 hours."* One fact per sentence, sequenced.

**C8. Numbers are converted into something imaginable.** `CORPUS_PATTERN`, general rather
than Bregman-specific. Voyager's annotator: *"we usually feel better when a number carries
with it a familiar point of reference"*, praising the translation of astronomical units into
"122 times as far from the sun as Earth". Qiu: 2.5 million km² → *"an area bigger than
Greenland"*. Bregman: a cigarette machine's output re-scaled from *"20,000 cigarettes per
minute"* to *"10 million per eight-hour shift"*; a scarcity effect re-expressed as *"between
13 and 14 IQ points"*. Reveley numbers the dead so a grandfather becomes *"Number 62"*.

**C9. Endings are often found upstream, not written harder.** `CRAFT_TEACHING` +
`CORPUS_PATTERN`. H9 confirmed, and by an unusually strong pairing. John McPhee, quoted in
TON's *Good Endings*: *"Look back upstream. If you have come to your planned ending and it
doesn't seem to be working, run your eye up the page and the page before that. You may see
that your best ending is somewhere in there, that you were finished before you thought you
were."* Independently, the Voyager Storygram annotator applies exactly that test to a
published piece and concludes *"It might have been better to end on the high note of the
second-to-last paragraph."* Two of twelve annotated exemplars are criticised for ending one
paragraph too late; none is criticised for ending too early.

**C10. Meaning may be implicit or explicit depending on reader need.** `CRAFT_TEACHING`.
H11 confirmed. Nut grafs are usually required but *"sometimes a nut is unnecessary,
especially if it becomes a crutch and doesn't work with the story… When it's a really strong
narrative and the story's just driving you, that can be strong enough"* (Sam Fromartz, FERN).
Sometimes a single quote serves as the nut. On the abstract apex: *"I try not to really force
those more abstracted ideals. Not every worm story is about justice"* (Sabrina Imbler). And
for contested subjects the opposite holds — see D2.

## 4. What the research disproved

**D1. "Good nonfiction opens concrete" is a house rule, not a law.** Belief 1 is
**weakened**. It is a good default in narrative feature writing: 10 of 12 control exemplars
open on a person, scene or dated event. But the two exceptions are instructive, and Bregman
— the owner's primary model — is *less* scene-first than the professional narrative control
group. Only about 5 of 15 Bregman openings are concrete-first. His most-read narrative piece,
*The real Lord of the Flies*, opens on a 20-word abstraction: *"For centuries western culture
has been permeated by the idea that humans are selfish creatures."* Andrew Grant's Voyager
lede is 12 words of pure abstraction — *"Humankind has officially extended its reach to the
space between the stars"* — and its annotator calls it a model of the form. Scientias opens
on the finding, not on anything concrete, in 14 of 25 articles.

The defensible version: **the reader should get something they can hold early, but "early"
may be the second or third sentence, and in argumentative and explanatory forms the thing
they hold first is often a question or a stake rather than an object.**

**D2. "Never announce the thesis" is false.** Belief 2 is **disproved as a general rule**.
Grant's Voyager piece states its whole significance in sentence one. Bregman's `BR-13` opens
*"This piece is about one of the biggest taboos of our times"* — maximum meta-announcement,
in the Guardian, by the writer the owner most admires. And on contested subjects the teaching
is emphatic in the other direction: *"the debate should be made clear right at the start of
the story, in the headline, dek, or — at the very latest — in the nutgraf. I think we really
owe it to our readers to explain upfront what they're getting into"* (Katarina Zimmer, TON).

The defensible version — and it is the campaign brief's own formulation, which the evidence
supports: **the idea should be stated when the reader needs the statement.** In `BR-14` the
thesis lands at 83% of the way through and is then repeated as the last line. It is neither
early nor absent. It is late and doubled.

**D3. The visible/invisible distinction is the wrong axis. Content transitions are taught
craft; outline transitions are genre-bound.** Belief 3 and H8 are **disproved**, and this
finding was itself revised once a source this pass had missed was read (see §5, X7).

The Open Notebook's *Good Transitions* teaches four **visible** devices approvingly: the
head-to-tail echo (repeat a word or concept from the previous paragraph's last sentence),
the contrast turn, the "But wait" reversal, and a dated launch-pad sentence after a section
break. It uses the word *signpost* as praise — *"The short, declarative sentence that begins
the next paragraph acts like a signpost for readers, signaling in uncomplicated language…"* —
and Robin Lloyd describes head-to-tail transitions as a deliberate control mechanism:
*"grabbing the reader and saying, 'Look, we're going to keep talking about this topic…'
You're controlling the reader's train of thought even more intentionally, more aggressively."*
Her caution is *use sparingly*, not delete-first.

So the axis is not visibility. It is what the transition points at:

- **Content transitions** point at the material. Visible, taught, used throughout narrative
  features.
- **Outline transitions** point at the article's own structure. Genre-bound to argument. Bregman signposts constantly and explicitly: *"Let me
show you why." "First, look at user growth." "Next, let's look at revenue." "Let me give you
three data points. One… Two… Three…" "So let's look for an analogy." "Three things, at
minimum. One:… Two:… Three:…"* The prestige narrative control group uses almost none of this;
its annotators praise the opposite — head-to-tail transitions that repeat a word from the
previous paragraph, and transitions so quiet that *"good braiding is almost unnoticeable"*.

Bregman's outline signposting (*"First, look at user growth." "Next, let's look at revenue."
"Three things, at minimum."*) runs at 0.051 per paragraph against 0.005 in the narrative
control group — a real 10× genre difference. The brief's hypothesis — *if a transition
announces the outline, delete before rewriting* — survives only for **outline** transitions in
narrative forms. Applied to content transitions it would delete the craft.

**D4. "Short sentences are clearer" is incomplete.** Belief 4 is **complicated**. Mean
sentence length does separate the samples (Bregman 15.3, Scientias 15.8, control exemplars
19.7 words) but variance separates them differently. Bregman's sentence-length standard
deviation is 8.3 against Scientias' 6.7 — the same mean, noticeably more rhythm. His 25th
percentile is 9 words and his 90th is 26. Accessibility is not shortness; it is a low clause
load with a wide length range. Emily Mullin, quoted in TON: *"Short sentences tend to be
punchier… On the other hand, winding, detail-bejeweled sentences invite the reader to imagine
and wander mentally."*

**D5. One-sentence paragraphs are a device, not a defect.** Belief 5 is **disproved as
stated**, and this is the campaign's clearest over-correction finding. `continuity.py`
diagnoses Jia's 33% one-sentence-paragraph rate as *"a slot that FORCES its sentence to
perform"*. The diagnosis of the Jia failure is right; the generalisation is not. Bregman
averages 11% one-sentence paragraphs and reaches 37% in one piece, and 8% of his paragraphs
are 15 words or shorter. Those short paragraphs are the load-bearing structure of his
argument essays: *"The deniers are us." / "But isn't it all a bubble?" / "So. What do we do?"
/ "Three things, at minimum." / "Genes can't be undone. Poverty can." / "It's the context,
stupid."*

What actually went wrong in Jia is visible in `continuity.py`'s own measurement: the
performing sentences were 0.90–0.93 similar to the architect's own prose fields. The defect
was **restatement of the scaffold in a prominent slot**, not the slot. PR #62 already fixes
the restatement. Suppressing the slot would remove the most Bregman-like device available.

**D6. "Every article needs a protagonist" is false.** Belief 6 is **disproved**. TON's
*Choosing Unconventional Main Characters* documents published work centred on an animal
(O-Six the wolf), a body part (Emily Willingham's *The Penis: A Life*), an everyday object,
and an abstract concept (Padavic-Callaghan's imaginary numbers, given a redemption arc). Also
relevant: Twilley's gravitational wave *"almost acts as a character"*. A concept can be the
carrier. And Barry-Jester's annotator warns of the opposite trap: statistics without a person
lose readers, so the choice is real and per-story.

**D7. Provenance in reader prose is not per se a defect.** Belief 7 is **narrowed** — and the
narrowing matters, because PR #62 enforces the broad version mechanically.

Against the broad rule: Yong's *"Speaking at a press conference today"* is praised —
*"Yong is identifying where he got this information from, which is important for readers in
case they want to track it down."* Qiu's *"In one unpublished study…"* is praised for flagging
the status. Waldman's fully transparent methodology block is praised at length: *"Editors
sometimes shy away from spelling this sort of stuff out to readers, worrying it'll 'bog the
reader down'… I totally disagree. By giving the reader the opportunity to explore our
processes and logic, we build trust."*

For the narrow rule, and strongly: Banaszynski, on background specifically — *"you don't need
to show your proof around background the way you show proof with new information. Specific
sourcing of widely acknowledged and available information isn't very helpful in a story."*

So the craft position is: **provenance about what the evidence *shows* can be reader-facing
and load-bearing; provenance about what the evidence *lacks* is the machine talking about
itself.** PR #62's ban on `does not (establish|say|state|tell|report|describe|show|prove)` is
exactly the right target. Its ban on the bare phrase `the evidence` is broader than the craft
evidence warrants — flagged, not to be fixed in this campaign.

## 5. What the research complicated

**X7. Our own transitions finding was too strong, and the V1 seed caught it.** The first pass
measured signpost-opener rates and concluded that visible signposting was near-absent from
narrative features. The measurement was right and the inference was too broad: the detector
was counting outline-announcing openers, and narrative features carry visible *content*
transitions the detector does not see. The Open Notebook source that settles this was in the
V1 seed list and not in ours. Recorded because a research pass that cannot find its own
over-reach is not worth much.

**And then the correction itself needed correcting.** A first revision of this section claimed
PR #62's `SIGNPOST_SHAPES` "flags exactly the class this source teaches as good craft." Tested
directly, that is false: of six devices the source praises, the detector flags zero; of the
four sentences the owner flagged in Jia, it flags four. The detector was better aimed than the
correction gave it credit for. What it did need was a published baseline instead of a threshold
at zero, because it does flag legitimate reader instruction in argument forms — and that has
now been implemented (`PR62_CRAFT_GAP_ANALYSIS.md` §18).

**X1. Question density is Bregman-specific, not a general accessibility trait.** This
corrects a mistake I made mid-campaign. A first pass showed Scientias asking 3.6 questions
per 1,000 words, close to Bregman's 5.1, which suggested question-asking was simply how
accessible prose works. It was an artefact: Scientias' page furniture includes the standing
line *"Uitgelezen? Luister ook eens naar de Scientias Podcast"*. After removing site
boilerplate, Scientias asks **0.91 questions per 1,000 words, median 0.00**, and the control
exemplars **0.87**. Bregman asks **5.06** — roughly 5.6× either comparison group. Direct
address shows the same shape: Bregman 20.9 per 1,000 words against 8.0 (controls) and 9.9
(Scientias). Bregman's interrogative, second-person manner is a personal signature. It is
available to borrow; it is not what makes prose accessible in general.

**X2. Pivot paragraphs are Bregman-specific too.** After cleaning, Scientias has **zero**
paragraphs of 15 words or fewer and a paragraph-length standard deviation of 15.9 against
Bregman's 25.1. Two different accessibility strategies: Bregman varies paragraph size
violently and uses tiny paragraphs as hinges; Scientias keeps a near-uniform 54-word
paragraph and does its pacing inside the sentence.

**X3. Bregman is not less abstract than prestige nonfiction — he is less tangled.**
Nominalisation density is effectively identical: Bregman 20.3 per 1,000 words, controls 20.2.
Proper-noun density is identical too (96.6 vs 97.4). What differs is clause load and sentence
length. This is direct support for H2: **the difficult noun stays; the syntax around it gets
simple.** *"Scarcity narrows your focus to your immediate lack"* keeps the concept and drops
the subordination.

**X4. Bregman uses about half as many quotes as the control group.** Quote-bearing paragraph
share: Bregman 0.25, controls 0.48, Scientias 0.23. His authority is carried by the author's
own voice and by footnotes, not by attributed speech.

**X5. Numbers are not sparse in Bregman — they are re-expressed.** Number density is the same
as the control group (11.8 vs 11.9 per 1,000 words). The difference is entirely in handling,
and it is not absolute: `BR-13` leaves *"In the United States, the figure is 188.8%"*
unexplained. Even the best practitioner of the move does not always make it.

**X6. Professional annotators spend most of their attention below the paragraph.** Of 421
Storygram annotations, a crude keyword coding leaves 45% outside every macro-structural
category — they are about a single verb, a single detail, one word. Sokol's Storygram contains
six separate annotations praising individual verbs. This is a caution about our own priors:
we have been designing macro-architecture, and the professionals reverse-engineering excellent
work spend most of their time on word choice and concrete detail. The coding is coarse and
the inference is soft, but the direction is worth noticing.

## 6. What we did not know before

**N1. The pivot paragraph.** A 4–15 word standalone paragraph carrying either the reader's
next question or a bare verdict, placed at a structural hinge. It is how Bregman creates the
breathing room the owner is asking for — not by lengthening explanation, but by cutting a
hole in the page. It is measurable: 8% of his paragraphs, 19% of which contain a question
mark. Nothing in our previous thinking named this.

**N2. Two named, incompatible background architectures.** The WSJ model and the braided
model. We have been designing one structure. The teaching is explicit that the choice
depends partly on *"the material available from reporting"* — that is, on evidence density,
which is exactly the variable the ledger measures.

**N3. The objection-as-paragraph.** Bregman writes the reader's counter-argument as its own
paragraph and then answers it: *"But isn't it all a bubble?"*, *"Now, the obvious objection:
of course an AI executive predicts explosive growth."*, *"Some skeptics, when they hear
this, say: but you can already google this stuff."* This is a distinct device from the reader
question. A question is curiosity; an objection is resistance. Both need answering, in
different places.

**N4. Scientias' de-interpretation move.** Scientias routinely tells the reader what a number
does **not** mean: *"Ook dat cijfer vraagt om voorzichtigheid: het betekent niet dat deze
mensen letterlijk 2,2 jaar langer leven."* / *"De percentages betekenen dus niet dat een baby
die weinig suiker krijgt automatisch 69 procent minder kans heeft…"* This is a negative
statement that serves the reader rather than the machine — a claim about the world's
interpretation, not about the evidence's silence. It is a category PR #62's negative-claim
handling does not currently distinguish. See `PR62_CRAFT_GAP_ANALYSIS.md` §9.

**N5. Scientias gives limitations their own real estate.** In `SC-09` five consecutive
paragraphs — roughly 30% of the article — are limitations, in short plain sentences, with no
hedging vocabulary: the patients were not typical brains, the electrode placement was
clinical not experimental, the direction of causation is open, the subjects were at rest, the
application is a plan. This is how a 650-word piece can be honest about uncertainty without
sounding evasive: uncertainty gets a section, not an adverb.

**N7. Scene provenance has three named tiers, and one of them is ours.** Lauren Kessler works
the taxonomy through a single published article: direct observation (*"I sat quietly in the
corner and took notes"*); a **debriefed observer** — a scene that *"reads like the product of
direct observation, but was not"*, built from a doctor's second-by-second notes read aloud,
follow-up questions, prior sight of the room, conversations with the daughter, having met the
dog; and recorded material (*"after I watched and rewatched the tape"*). The governing rule:
*"A scene can be written only if the journalist has the material, however that material is
ever-so-carefully gathered."* Sebastian Junger's *The Perfect Storm* feature was reported
*"entirely through second-hand accounts and materials"* — a canonical narrative built with zero
direct observation. Tier 2 is where Crip Minds actually operates, because it works from
documents that are themselves observer records. Operational form: **a scene may be written when
a ledger fact is an observer record of that moment, at the granularity being written.**

**N8. The harder the material, the simpler the structure should be.** Tom French: *"What you
want is for the structure to be as simple as it can be so that the reader has the best chance
possible to think about the complexity of what you're trying to get across. The more complex
the material, the simpler the structure should be."* Sarah Scoles independently: *"it's good
for the reader, if you're writing about complicated things, to go with a chronological
structure."* And New Yorker writers reportedly *"can use any structure they want, but at the
end of the day they will change it back to chronological."* This argues against elaborating
the Story Architect for difficult material.

**N9. Explanation can be replaced by the story of the explanation.** Carl Zimmer: *"it's often
a good move to disperse pieces of the explanation throughout your story… Tell the story of the
explanation, rather than giving the explanation itself."* Also from Zimmer, the sharpest
statement of the failure mode: *"If you spend all your time explaining rather than telling a
story or advancing an argument, the structure of your writing will collapse under that
explanatory weight."*

**N10. The more dramatic the material, the plainer the telling.** Two independent
professionals: Kessler — *"unadorned by adjectives, adverbs, metaphors, whatever. The moments
themselves were dramatic; I did not want to force more drama into the retelling"* — and the
ProPublica annotator: *"The more intrinsically dramatic the scene you're describing, the more
plainly and simply you're required to tell it."*

**N6. Reconstruction is a licensed technique with an explicit ethical boundary.** Maxmen's
Ebola narrative reads as witnessed and is not: *"it's important to not try to 'trick' readers
by making it sound like we're present when we're not."* Oaster reconstructs a 1950s scene down
to the smell of smouldering alderwood, from oral history. Blakeslee gives a wolf real interior
dimension *"without falling into the trap of speculatively assigning motives or specific
emotions"* — possible because *"the extensive information available in the reports"* supported
it. Narrative density is a function of evidence density. That is a craft principle, not just
a compliance rule.

## 7. What remains unknown

- **Whether pivot paragraphs survive translation of register.** All of Bregman's are in a
  first-person, spoken-lecture voice. Whether the device works in a third-person Crip Minds
  article is untested.
- **Whether the reader-question model can be validated without readers.** Every confirming
  source is a human reporting their own experience of reading. We have no evidence that a
  model can predict where a reader's question falls.
- **Provenance of Bregman's English.** Six of fifteen texts carry explicit or probable
  translation and additional editing. Structural findings are unaffected. Lexical findings are
  labelled accordingly throughout — see the Bregman profile's provenance table.
- **Paragraph structure of the control exemplars.** Only 2 of 12 have reliable paragraph
  boundaries; the Storygram layout merges paragraphs into blocks (median 130 words vs Ed
  Yong's 80). All control paragraph metrics are reported with n=2 and should not be used.
- **Whether omission can be inferred.** We can see that Bregman's Benjamin Lay essay carries
  38 footnotes for 5,072 words of prose and that Sokol's annotator says *"what a science
  journalist leaves out is as important as what they leave in"*. We cannot see the notes that
  were discarded. §30 of the brief asks a question the public record cannot fully answer.
- **Whether any of this improves Crip Minds output.** Nothing here was tested against a
  generation. That is the next campaign, not this one.

## 8. The one place craft and safety could collide, and why they do not

The brief anticipates the collision: professional narrative craft wants scene, sensation and
interiority, and Crip Minds forbids inventing any of them. The research says the collision is
avoidable, and says so from inside the craft literature rather than from our rulebook.

Every vivid reconstruction in the control group is **reported**, and the annotators treat the
reporting as the achievement. Paliwal asked a grieving brother what kind of flower it was and
where it came from, so that *"Tabish ran out and plucked a rose from a garden nearby"* could
be written. Twilley pressed for unusual sources of detector noise until she got *wolves*.
Oaster sought out the smell of smoking sheds in oral histories. Mullin asks *"How big is it?
What colour? Is it soft? Rigid? Cool to the touch?"*

So the correct response to "we do not have the evidence for this scene" is the brief's own
answer — research more, or choose another form — and that is also what the craft literature
says. Vividness is an output of acquisition, not of generation. The engine's constraint is not
in tension with excellence; it is in tension with *cheap* excellence.

## 9. Held-out prediction

Stated so this model can be wrong about an article nobody has read. See
`NONFICTION_REVERSE_ENGINEERING_V2.md` §7 for the full set. In short, for an unseen strong
accessible nonfiction piece this model predicts: 45–62% single-clause sentences; under 6% of
sentences carrying four or more clause boundaries; a first concrete referent within the first
three sentences even when sentence one is abstract; an explicit statement of the idea either
in the first 10% or after the 70% mark but rarely between; and an ending whose final
paragraph could not be deleted without losing a concrete referent introduced earlier.
