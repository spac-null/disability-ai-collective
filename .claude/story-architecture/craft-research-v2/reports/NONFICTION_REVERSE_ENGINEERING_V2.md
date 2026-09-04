# Nonfiction reverse engineering v2

Paragraph-level structural maps for five texts in five different forms, plus the
reader-question analysis, the mode necklaces, and the held-out predictions.

Mode labels: `SCENE` `EVENT` `ACTION` `SUMMARY` `CONTEXT` `EXPLANATION` `ARGUMENT`
`REFLECTION` `EVIDENCE` `COUNTERPOINT` `TRANSITION` `ENDING` `PIVOT`.
Abstraction: `LOW` (person, object, action, place, physical mechanism, event) ·
`MID` (institution, category, process, generalised pattern) · `HIGH` (theory, moral idea,
political concept, philosophical meaning).

Where paragraph boundaries could not be recovered reliably, that is stated and the map is
made at section level instead. Which text has which is in
`../sources/craft_sources_v2.jsonl` under `paragraph_boundaries_reliable`.

---

## 1. `BR-14` — EXPLANATORY_FEATURE
*Rutger Bregman, "Why do the poor make such poor decisions?", The Correspondent. 2,530 words,
50 paragraphs. Translated (Manton/Moore) and additionally edited (Mushett) — structure is
analysable, wording is not attributable.*

This is the most instructive text in the whole corpus for Crip Minds, because it has to make
a piece of behavioural-science research legible and it has no scene material after paragraph 3.

```
 0  EVENT        13 Nov 1997, a casino opens south of the Great Smoky Mountains   LOW
 1  CONTEXT      what kind of casino, whose land                                   LOW→MID
 2  EVIDENCE     the profits, and what the tribe built with them                   MID
 3  EVENT        a Duke professor had been studying local children since 1993      LOW
 4  PIVOT        "But the question still remained: which was the cause, and        MID
                  which the effect?"  (13 words, own paragraph)
 5  CONTEXT      at the time, mental illness was being attributed to genes         MID→HIGH
 6  EVIDENCE     behavioural problems fell                                          MID
 7  EVIDENCE     Costello's own disbelief at the size of the effect                 LOW
 8  EVIDENCE     the younger the escape from poverty, the better the outcome        MID
 9  EXPLANATION  the mechanism: money let parents parent                            LOW
10  EVIDENCE     they were not working less — the hours were the same               LOW
11  ARGUMENT     nature or culture? both                                            HIGH
12  PIVOT        "Genes can't be undone. Poverty can."  (6 words)                   HIGH
13  PIVOT        "A world without poverty – it might be the oldest utopia around."  HIGH
14  COUNTERPOINT the hard questions: crime, obesity, debt                           MID
15  EVIDENCE     the statistics that make the hard questions look justified         MID
16  CONTEXT      the entrenched notion that the poor must fix themselves            HIGH
17  CONTEXT      Thatcher: poverty as a "personality defect"                        LOW→HIGH
18  PIVOT        "But is that all there is to it?"  (8 words)                       MID
19  COUNTERPOINT "What if the poor aren't actually able to help themselves?"        HIGH
20  CONTEXT      and it is Eldar Shafir asking — the expert arrives at 40%          LOW
21  PIVOT        "It's the context, stupid."  (4 words)                             HIGH
22  EXPLANATION  Shafir's ambition: a science of scarcity                           MID
23  PIVOT        "We behave differently when we perceive a thing to be scarce"      MID
24  EXPLANATION  scarcity is a perception, not a quantity                           MID
25  EXPLANATION  it applies to time, money, friendship, food — and it has benefits  MID
26  EXPLANATION  the drawback: it narrows focus to the immediate lack               MID
27  EXPLANATION  ANALOGY — a computer running ten heavy programs, freezing          LOW
28  EXPLANATION  the term is coined here: "mental bandwidth"                        MID
29  ARGUMENT     the distinction: you can't take a break from poverty               MID
30  EVIDENCE     "between 13 and 14 IQ points… comparable to losing a night's sleep" MID
31  REFLECTION   "we just put two and two together"                                 MID
32  EVIDENCE     the mall experiment: cheap repair versus expensive repair          LOW
33  EVIDENCE     the cognitive test results                                          MID
34  COUNTERPOINT the confound they could not fix                                     MID
35  EVIDENCE     the Indian sugarcane harvest — the same people, rich then poor      LOW
36  PIVOT        "So how did they do in the experiment?"  (8 words)                  MID
37  EVIDENCE     substantially worse, and not because they had got dumber            MID
38  ARGUMENT     fighting poverty has benefits we have been blind to                 HIGH
39  EVIDENCE     back to the Cherokee: the casino cash paid for itself                MID
40  PIVOT        "So what can be done?"  (5 words)                                   MID
41  SUMMARY      the nudges on offer: aid paperwork, pill boxes                       MID
42  ARGUMENT     but a nudge treats the symptom                                       HIGH
43  PIVOT        "Poverty is not a lack of character. It's a lack of cash"  (12 w)    HIGH
44  COUNTERPOINT Shafir's own blank look at the suggestion                            LOW
45  EVIDENCE     what it would cost, and what poverty already costs                   MID
46  ARGUMENT     education won't help until they are above the line                   MID
47  PIVOT        "It doesn't have to be this way."  (7 words)                          HIGH
48  CONTEXT      Samuel Johnson on poverty and liberty                                 MID
49  ENDING       "It's a lack of cash."  (5 words)                                     HIGH
```

**Mode necklace** (S = scene/event, M = summary/context, E = explanation/evidence,
R = argument/reflection, · = pivot):

```
S S E S · M E E E E E R · · M E M M · R M · E E E E E E R E R E E R E R E R · M R · R E R · M ·
```

**Register movement:** `LOW LOW MID LOW · MID MID LOW MID LOW LOW HIGH · · MID MID HIGH HIGH ·
HIGH LOW · MID · MID MID MID LOW MID MID MID MID LOW MID MID LOW · MID HIGH MID · MID HIGH ·
LOW MID MID · MID HIGH`

**Reader-question movement.** This is where the text's real design lives.

| after | reader now knows | reader now wonders | text gives next | verdict |
|---|---|---|---|---|
| P3 | a casino made a poor community better off, and someone was measuring | did the money cause it, or were they already improving? | the question itself, as a 13-word paragraph | **answers a natural question by naming it** |
| P11 | both genes and poverty matter | so what? | *"Genes can't be undone. Poverty can."* | **creates a better question** — what do we do about the one we can change? |
| P17 | that the standard view blames the poor | is the standard view right? | *"But is that all there is to it?"* then *"What if the poor aren't actually able to help themselves?"* | **converts a moral judgement into an empirical question** |
| P19 | that the question is open | who is asking this, and can I trust them? | Shafir, Princeton, and a slogan | **answers exactly the question just raised** |
| P26 | that scarcity narrows focus | what does that mean physically? | the overloaded-computer analogy | **answers before naming** |
| P27 | the felt experience of the mechanism | what is this called? | *"mental bandwidth"* | **term as a label on an existing understanding** |
| P30 | that it costs 13–14 IQ points | is that a real experiment or an inference? | the mall study, then its confound, then the Indian natural experiment | **anticipates the sceptic without being asked** |
| P34 | that the mall study had a hole | so is the finding safe? | the sugarcane harvest — same people, two states | **closes the hole the reader just found** |
| P42 | that nudges are inadequate | then what is adequate? | the thesis, at 83% | **the statement arrives when the reader needs it** |

Zero instances of background arriving before the reader had a use for it.

**Why it works.** Two natural experiments do all the evidential load-bearing, one concept is
built up over six paragraphs before it is named, and ten short pivot paragraphs mark every
place the reader would otherwise get lost. The thesis is withheld to 83% and then said twice.
No paragraph carries more than one job.

**Ending upstream test.** It cannot end one paragraph earlier: P48 (Samuel Johnson) without
P49 leaves the argument on an 18th-century quotation. Two paragraphs earlier is worse — P47 is
a pivot, not an ending. This is a case where the last paragraph is load-bearing.

---

## 2. `BR-02` — ARGUMENTATIVE_ESSAY
*"An Inconvenient Truth About AI", Substack. 4,630 words, 105 paragraphs.*

Section-level map, because 105 paragraphs is too many to be legible and the design is sectional.

```
 0–8    ANALOGY FRAME    2006, Gore, the CO2 line, the denial sequence     LOW→MID
                         ends on the 4-word pivot "The deniers are us."     HIGH
 9–19   COUNTERPOINT     Chomsky, Bender, Gebru — then a list of 6 things   MID
                         the "stochastic parrot" has done                    MID
20–24   EVIDENCE         the METR curve, 30 seconds → 12 hours              MID
                         explicitly rhymed against Gore's curve              HIGH
25–33   REFLECTION       "have you actually used it?!" + the capex numbers  LOW→MID
34–46   OBJECTION 1      "But isn't it all a bubble?" (6-word pivot)        MID
                         → the sceptics' ammunition → user growth →
                         Anthropic's revenue ladder → the railway analogy
47–52   ARGUMENT         the goalposts have moved; recursive self-improvement HIGH
53–61   CONCRETE PROOF   Relman's night; three data points; Aum Shinrikyo;   LOW
                         Tokyo, March 1995, five bags of sarin
62–64   EVIDENCE         AISI, Mythos, and a company withholding a product   MID
65–75   ANALOGY          "And that brings us to the deepest risk. Power."    HIGH
                         resource curse → the fiscal bargain → intelligence
                         curse → concentration of wealth
77–90   PRESCRIPTION     "So. What do we do?" → what not to do → "So what    MID
                         does work?" → "Three things, at minimum."
91–101  VISION           Utopia for Realists, Keynes, the 15-hour week       HIGH
102–106 ENDING           back to Gore's scissor lift, then the direct        HIGH
                         address: "Stop the denial… And dare to fight"
```

**Necklace:** `M M E R E R M E R E S S S E R R M R H`

**Why it works.** One frame (Gore's curve) opens, is rhymed at 19%, and closes at 96%. Every
abstract section is preceded or followed by a concrete sequence that earns it. Objections are
raised in the reader's voice, as their own paragraphs, at 31%, 34% and 51%. Nine visible
signposts. Eight pivot paragraphs.

**Ending upstream test.** It could end at P104 (*"Stop the denial. Stop pretending this is
hype."*) and lose little; P106 (*"And dare to fight for a wildly better future."*) is a
peroration rather than a necessity. This is the one Bregman text in the sample where McPhee's
test finds slack.

---

## 3. `CX-02` — EXPLANATORY_FEATURE
*Ed Yong, "North Atlantic Right Whales Are Dying in Horrific Ways", The Atlantic. 1,316
words, 17 paragraphs. Paragraph boundaries reliable.*

```
 0  PERSON       "She was called Punctuation…" — a named whale, in past tense  LOW
 1  EVENT        two more dead, both named for their scars                      LOW
 2  EVIDENCE     "dead in less than a month" — why you are reading this now     MID
 3  EVIDENCE     "Honestly, I don't have the words" — the expert is speechless  LOW
 4  PIVOT        "How much death can a species tolerate?"                       HIGH
 5  EVIDENCE     "Six have died this month alone." + life span 80–100 years     MID
 6  SUMMARY      the two causes: ship strikes, entanglements                     MID
 7  EVIDENCE     Punctuation's own history: five entanglements, two strikes      LOW
 8  PIVOT        "Ship strikes. Entanglements."                                  MID
 9  REFLECTION   "There is something almost euphemistic about these terms"       HIGH
10  EVIDENCE     the injury catalogue: fractured skulls, broken spines           LOW
11  EVIDENCE     an expert on why nobody sees it happen                          MID
12  CONTEXT      whaling history, the 1937 ban, the partial recovery             MID
13  EXPLANATION  what regulation can do; and warming pushing them north          MID
14  COUNTERPOINT some of this year's dead were found outside protected zones     MID
15  EVIDENCE     press conference; the 90%-of-entanglements claim                 MID
16  ENDING       "we do need to know where they are"                             MID
```

**Necklace:** `S S E E · E M E · R E E M E M E M`

**Reader-question movement.**

| after | wonders | gets | verdict |
|---|---|---|---|
| P3 | how bad is this, in aggregate? | the rhetorical question, then the count | **answers by naming the question** |
| P9 | what do those euphemisms actually cover? | the injury catalogue | **answers immediately, concretely** |
| P11 | why aren't there more whales? didn't I hear they were recovering? | the whaling history | **the annotator names this exact question** |
| P13 | can anything be done? | the regulatory prongs, then their failure | **answers, then complicates** |

**Why it works.** Orientation is a *person* — a named animal with a family and a death date —
and the abstraction ("how much death can a species tolerate") is placed at the exact point
where the reader has enough particulars to ask it. Two pivot paragraphs. No scene: nothing is
witnessed anywhere in the piece. It is entirely explanation and evidence, and it reads as a
narrative because the whale has a name and a history.

**This is the closest analogue in the corpus to what Crip Minds needs to be able to write.**
It has no witnessed scene, no interiority, no invented perception, and it still has a
protagonist and an emotional arc — built purely out of records that already existed.

---

## 4. `CX-12` — SCIENCE_NEWS
*Andrew Grant, "At Last, Voyager 1 Slips into Interstellar Space", Science News. 993 words,
16 paragraphs. Boundaries reliable.*

```
 0  ARGUMENT     "Humankind has officially extended its reach…" — 12 words     HIGH
 1  EVENT        the date, the instrument, the journal                          MID
 2  EVIDENCE     18.2bn km, translated: "122 times as far from the sun as Earth" MID
 3  EVIDENCE     Stone confirms the claim in his own voice                       MID
 4  EXPLANATION  dense fog versus thin mist                                       LOW
 5  SUMMARY      "patience, clever detective work and a heavy dose of luck"      MID
 6  EXPLANATION  plasma as a flood of hot charged particles                       LOW
 7  EXPLANATION  the heliopause, glossed inside the sentence                      MID
 8  EVENT        July 2012: the count plummets — then rebounds. False alarms      MID
 9  COUNTERPOINT "Stone and his colleagues resisted that conclusion."             MID
10  EVIDENCE     the plasma instrument died near Saturn 33 years ago              LOW
11  ACTION       Gurnett finds a way anyway — we watch him do it                  LOW
12  EVIDENCE     "50 times as dense" — the calculation, distilled                 MID
13  COUNTERPOINT "Not everyone agrees, including a few holdouts on the team"      MID
14  SUMMARY      seven years of plutonium left; what else it might find           MID
15  ENDING       Aug 25 2012 — also the day Neil Armstrong died                   HIGH
```

**Necklace:** `R M E M E M E M M R E S E R M H`

**Why it works, and where it doesn't.** A 12-word abstraction opens it and the annotator calls
it a model lede — this is the corpus's clearest counterexample to "open concrete". Every
technical term is glossed in the same sentence. The mystery structure (false alarms →
scepticism → dead instrument → workaround) is drawn from the actual chronology, not imposed.
The debate is folded into the momentum rather than made the subject.

**Ending upstream test — the important case.** The annotator says outright: *"Mentioning Neil
Armstrong and his passing in this final phrase of the story strikes an awkward chord. It might
have been better to end on the high note of the second-to-last paragraph."* A professional
annotator applying McPhee's test to a published piece and finding it one paragraph too long.

---

## 5. `CX-09` — NARRATIVE_FEATURE
*B. "Toastie" Oaster, "Pacific Lamprey's Ancient Agreement with Tribes Is the Future of
Conservation", High Country News. Section-level map: paragraph boundaries are **not** reliable
(Storygram reprint merges paragraphs; median block 105 words).*

```
S1  WORLD-BUILDING     mid-1950s Celilo Falls, before its destruction        LOW
                       river → fish → families → one boy, mid-activity
S2  RUPTURE            "In the end, it was Celilo Falls that drowned."       LOW→MID
S3  PRESENT SCENE      last July, an eel dance in a park in Oregon           LOW
S4  CONCEPTUAL WORLD   Wewa on fact becoming legend; animals' agreements     HIGH
                       with humans — the first direct quote in the piece
S5  EXPLANATION        the lamprey: 450m years, understudied, disdained      MID
S6  CONTEXT            oral history; the trails; 90% decline; the dams       MID
S7  EXPLAINER→SCENE    eeling technique braided into a 4am boat trip         LOW
S8  PEOPLE             the crew's humour, the teenagers' ambivalence          LOW
S9  IMPLIED FIRST      "When you dunk in, you immediately feel slippery eel   LOW
    PERSON             skin slithering between your legs"
S10 GRIEF              Lewis's brother drowned at Lake Celilo                 LOW
S11 EXPOSITION         it is not the harvest that threatens them — it's dams  MID
S12 CALLBACK           Slockish and the ranger, placed late deliberately      LOW
S13 FUTURE             crews carrying eels past the dams by hand              LOW
S14 ENDING             children releasing eels; then back up to the falls     LOW→HIGH
```

**Necklace:** `S S S R E M S S S S E S S H`

**Why it works.** The abstract apex ("an ancient agreement" rather than "a symbiotic
relationship") is introduced as a *character's* worldview at S4, not as the writer's thesis,
and every later section is measured against it. The braiding of explainer into scene is, in the
annotator's words, *"almost unnoticeable"*. Numbers are used twice in the whole piece and land
hard because of it. The structure is a mirror: falls → fish → families → one child at the
opening, one child → fish → falls at the close.

**Reconstruction note.** The 1950s opening — the smell of smouldering alderwood, sherbet-coloured
slabs of fish, a boy in bib overalls — is entirely reconstructed from oral history and records.
The annotator flags this explicitly as a reporting achievement: *"these details are about a
time in the past, so the writer had to seek them out."*

---

## 6. Cross-form summary

| | BR-14 explanatory | BR-02 argument | CX-02 explanatory | CX-12 news | CX-09 narrative |
|---|---|---|---|---|---|
| opening | dated event | direct address → dated event | person (animal) | explicit thesis | scene (reconstructed) |
| nut / orientation | none; a question at 8% | thesis frame at 7% | question at 24% | sentence 1 | none; worldview at S4 |
| thesis | delayed to 83%, repeated | repeated throughout | absent | first sentence | emergent |
| signposting | 6 visible | 9 visible | none | none | none |
| pivot paragraphs | 10 | 8 | 2 | 0 | 0 |
| scene present | 3 paragraphs | 4 paragraphs | **none** | none | most of it |
| ending type | thesis + callback | moral + call | quote | date coincidence (criticised) | scene + callback |
| could end earlier? | no | yes, at 98% | no | **yes** — annotator says so | no |

There is no single architecture here. The only things constant across all five are:
(a) the reader gets something they can hold within three sentences; (b) explanation follows a
reason to want it; (c) the ending returns to something introduced earlier.

## 7. Held-out predictions

What this model predicts for a strong accessible nonfiction article nobody in this campaign
has read. Stated so it can fail.

1. **Clause load.** 45–62% of sentences will carry a single clause boundary; fewer than 6% will
   carry four or more; commas per sentence will be between 0.5 and 1.4. *(Range covers all
   three samples; a text outside it is either denser than prestige nonfiction or thinner than
   Dutch science news.)*
2. **Sentence range, not sentence length.** Mean sentence length will fall between 12 and 23
   words, and the interquartile range will be at least 8 words wide. A text with a mean of 15
   and an IQR of 4 will read as flat.
3. **First concrete referent.** A person, object, place, date or physical action will appear by
   sentence 3, **even if sentence 1 is abstract**. This is the corrected form of "open
   concrete", and it is the prediction most likely to be falsified — I expect it to hold in
   roughly 12 of 15 cases, not 15 of 15.
4. **Explicit statement placement.** If the idea is stated explicitly, it will appear either in
   the first 10% or after the 70% mark. The 20–60% band will be comparatively empty. *(Observed:
   BR-13 at 2%, CX-12 at 1%, BR-14 at 83%, BR-02 at 7% and repeated; and contested-subject
   teaching pushes to the front.)*
5. **Ending anchoring.** The final paragraph will contain at least one concrete referent
   introduced earlier in the piece. Where it does not, an annotator will criticise it. *(This is
   the one prediction the corpus has already tested twice and passed twice — CX-12 and CX-01
   both end without an earlier concrete referent and both are criticised for it.)*
6. **Term timing.** For any term needing a gloss, the gloss will be within one sentence of the
   term or will precede it. Front-loaded definitional paragraphs will be rare.
7. **Signposting tracks form.** Visible signposting (*"First… Next… Three things"*) will
   correlate with argumentative and lecture forms and be near-absent in narrative features. A
   narrative feature with heavy signposting will read as constructed; an argument essay without
   it will read as hard to follow.
8. **Question density is authorial, not formal.** Question density will vary more between
   authors than between forms — except that within one author it will roughly double from
   narrative to explanatory work.
9. **Numbers.** Most quantities will be compared, translated or attached to a person; but at
   least one per long article will be left raw, including in excellent work.
10. **Pivot paragraphs are optional.** Texts with paragraph-length SD above ~22 words will use
    short standalone paragraphs at hinges; texts below ~18 will not use them at all, and both
    can be excellent.

**A principle that only explains Jia after the fact is marked weak.** Applying that test to our
own findings: the one-sentence-paragraph diagnosis in `continuity.py` is a *post-hoc* Jia
explanation and it fails prediction 10 — so it is marked weak here, and §5 of
`CRAFT_EVIDENCE_V2.md` treats it as an over-correction. The reader-question finding is not
post-hoc: it was established from teaching material and from twelve texts Crip Minds had no
part in, before PR #62 was read.
