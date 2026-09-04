# PR #62 craft gap analysis — read-only

Comparison of PR #62's contracts against the craft evidence. **No implementation code was
changed and none should be changed on the basis of this document.** Several items are marked
as things that should explicitly *not* change.

State at time of analysis:

```
origin/main                        40be3486c218e8ba766ade4866286a5b7a33fad8
origin/feat/story-architecture     b447a82850a9a21ae426447478876eba9d2cae00
PR #62                             OPEN, MERGEABLE, 99 files, +9,178 lines, no deletions
local main                         732c84f9 — DIVERGED from origin/main, not touched
```

Format per component: current behaviour · craft evidence · match/mismatch/unknown · risk ·
minimal future change · confidence.

**Revised after V1 seed artifacts were supplied.** Three sections changed: §10(d) on the
signpost detector is now better supported, §13 gains two items, and §14 gains a ninth
protected item. One new section (§17) records what the seed changed. Full adjudication:
`V1_V2_COMPARISON.md`.

---

## 0. The calibration result

Before the component walk, the one measurement that changes how the rest should be read.

PR #62's `continuity.writtenness()` was built from one article. I ran it, unmodified, against
15 Bregman texts and 12 professionally-annotated exemplars — 1,181 paragraphs of published
prose it was never designed for.

| | Jia pre-audit | Bregman (n=15) | control exemplars (n=12) |
|---|---|---|---|
| `solo_ratio` (one-sentence paragraphs) | **0.33** | mean 0.11, **range 0.00–0.37** | mean 0.09, **range 0.00–0.32** |
| signpost openers per paragraph | **0.333** | **0.051** | **0.005** |
| negative-shape sentences per paragraph | — | 0.043 | 0.059 |

**`solo_ratio` does not discriminate.** Jia's 0.33 sits inside the published range. Three texts
in this corpus meet or exceed it: Bregman's Harvard fellowship piece (0.37), his self-help
piece (0.33), and Annie Waldman's ProPublica investigation (0.32). A metric on which excellent
published work and the flagged draft are indistinguishable cannot be the diagnosis.

**Signpost rate discriminates powerfully.** Jia opens a third of its paragraphs with a
signpost shape. Bregman — who signposts more than anyone else in this corpus, and whose
signposting is a legitimate genre convention (F-13) — does it at one paragraph in twenty. The
narrative control group does it at one in two hundred. Jia is 6.6× the most signposting
published author in the sample and 66× the narrative exemplars.

**Negative-shape sentences are normal in published prose** at about one per seventeen
paragraphs, slightly *more* often in the control exemplars than in Bregman. The scanner is
correctly built as a report for adjudication. If it ever became a gate it would reject
professional work.

So: the writtenness module's *diagnosis* names the wrong variable and its *other* signal is
excellent. That inversion is the highest-value finding in this document.

---

## 1. Ledger (`ledger.py`)

**Current behaviour.** The single origin of factual permission; narrows candidates to the
researched subject; everything downstream reads facts by id.

**Craft evidence.** No craft source speaks to this, and none needs to. But F-23 is adjacent:
the choice between the two named background architectures depends partly on *"the material
available from reporting"*, and the ledger is the only component that knows what the material
is. F-19 makes the same point from the safety side: narrative density is a function of evidence
density, and the ledger is where evidence density lives.

**MATCH**, and structurally well-placed. **Risk:** none identified. **Minimal future change:**
none. **Confidence:** HIGH.

---

## 2. Story Finder (`narrative_yield`, `validate_candidate`)

**Current behaviour.** Scores candidates out of 11 on carrier, concrete opening, real change,
causal support, tension and discovery, with penalties for concept-only spines and for having no
evidence. `CARRIERS = person, object, event, place, process`.

**Craft evidence.** `CARRIERS` is well supported (F-15): the teaching literature documents
published work centred on an animal, a body part, an everyday object and an abstract concept
given an arc, and in this corpus a named whale, a gravitational wave and a capability graph all
carry pieces. The `concept_only_penalty` phrase list is also well aimed — *"this reveals / this
reframes / reminds us"* is exactly the register the annotators never praise.

**MATCH with one qualification.** The `concept_only_penalty` of −2 assumes a concept spine is
worse than a physical one. F-15 says a concept can be the protagonist if it is given an arc —
Padavic-Callaghan's imaginary numbers get a redemption narrative, complete with side characters
(negative and irrational numbers). What makes a concept spine bad is not that it is a concept;
it is that *"this reveals"* is a stance rather than a change. The penalty is currently attached
to the wrong feature: it fires on the vocabulary, which happens to correlate.

**Risk:** LOW. The correlation is good enough that the penalty mostly fires correctly.
**Minimal future change:** none required. If revisited, the discriminating question is whether
the concept undergoes a change, not whether it is a concept. **Confidence:** MEDIUM.

---

## 3. Worth Gate (`validate_lens`, lens verdicts)

**Current behaviour.** Five verdicts. Two are publishable; `WEAK_ANALOGY`,
`NO_PLAUSIBLE_LENS` and `GREAT_GENERAL_STORY_WRONG_PUBLICATION` are holds. A publishable lens
must name a mechanism, cite evidence, say what it changes, and avoid an `EMPTY_LENS` phrase list.

**Craft evidence.** The ability to answer "wrong publication" is unusual and correct. The
`EMPTY_LENS` list (*"faces barriers", "reminds us that", "we are all"*) targets exactly the
gesture-instead-of-work move. And F-10 supports requiring the lens to do interpretive work.

But the ladder-of-abstraction teaching adds something the gate cannot express: *"I try not to
really force those more abstracted ideals. Not every worm story is about justice"* (Imbler).
And: *"How high you ultimately climb will depend on the nature of the story, as well as the
outlet and audience."*

**MISMATCH, narrow but real.** The gate's only outputs are *a lens strong enough to publish*
or *a hold*. It cannot say *this is a legitimate piece whose apex is low* — an explanatory
article that stays at MID, ends on a consequence rather than a reframing, and earns its place
by making something legible rather than by reinterpreting it. Ed Yong's whale piece (`CX-02`)
is exactly that article: it has no thesis, no reframing, and no interpretive turn. It is
excellent, and this gate would hold it.

**Risk:** MEDIUM — the failure is invisible, because a held article produces no output to
inspect. Over time the gate selects for a single altitude of piece.
**Minimal future change:** a sixth verdict for "publishable at low altitude", or a declared
apex level on the existing verdicts. Not to be built on this evidence alone; the question is
editorial, not technical.
**Confidence:** MEDIUM.

---

## 4. Story Architect — `article_type`

**Current behaviour.**
`ARTICLE_TYPES = (NARRATIVE_ARTICLE, SHORT_NARRATIVE, BRIEF, HOLD_NO_STORY, HOLD_WRONG_PUBLICATION)`.
The legacy Article Form component (FORM-1.3) is marked `LEGACY / NOT REMOVED` and is not used
by the experimental path.

**Craft evidence.** F-05, and it is the strongest structural mismatch in this document. The
three live values are **a length scale, and all three are narrative.** The craft evidence says
form varies along a different axis, and that the structural consequences are large:

| decision | narrative feature | explanatory feature | argumentative essay |
|---|---|---|---|
| opening | person / scene / dated event | finding, question or person | question, thesis or shared memory |
| background | braided, phrase by phrase | WSJ model: a block, then chronology | woven into the argument |
| signposting | near zero (0.005/para observed) | low | high and legitimate (0.05/para observed) |
| thesis | absent or emergent | delayed, 70–90% | announced and repeated |
| nut graf | often none | usually yes | the whole piece is one |
| pivot paragraphs | rare | present | heavy |

PR #62 cannot express any row of that table. Every article gets the narrative column.

**MISMATCH — the highest-value gap.** **Risk:** HIGH. Every downstream contract inherits the
narrative assumption: `opening_object_or_event` is required, beats must have concrete carriers,
signposting is treated as writtenness. An explanatory piece cannot be built by this
architecture even when the material is explanatory, which is most of the time for Crip Minds.

**Minimal future change:** the change is *not* to add a form taxonomy to `ARTICLE_TYPES`. It
is to make the two or three genuinely form-dependent constraints conditional rather than
universal — specifically the opening requirement (§5) and the signposting signal (§10). A form
field with no consequences would be scaffolding; conditional constraints are the actual content
of the finding. **Confidence:** HIGH.

---

## 5. Story Architect — `opening_object_or_event`

**Current behaviour.** Required. `validate_architecture` fails with *"opening_object_or_event
missing -- openings must be concrete"*.

**Craft evidence.** F-11. A strong default, not a law. 10 of 12 control exemplars open
concrete; Bregman does so in about 5 of 15; Scientias opens on the finding in 14 of 25; and the
two clearest counterexamples are both *praised by professional annotators* — Grant's 12-word
abstraction (*"Humankind has officially extended its reach to the space between the stars"*)
and Quammen's opening question about whether we should visit a place at all.

The defensible version is the *first concrete referent by sentence three*, which held in 12 of
15 Bregman texts including the three with abstract first sentences.

**MISMATCH in strength, not in direction.** The constraint is right about what serves readers
and wrong to be absolute. **Risk:** MEDIUM. It forecloses the explanatory and argumentative
forms at the first gate, which compounds §4.

**Minimal future change:** relax from *the opening must be a concrete object or event* to *a
concrete referent must appear within the first three sentences*. This preserves everything the
constraint was protecting and stops it from mandating one form.
**Confidence:** HIGH.

---

## 6. Story Architect — beats and `why_reader_wants_next`

**Current behaviour.** ≥2 beats; each needs a `concrete_carrier`; each but the last needs
`why_reader_wants_next`; `facts_allowed` must be in the frozen evidence and declared in
`use_facts`.

**Craft evidence.** F-01, the best-evidenced finding in the campaign, and PR #62 is the only
architecture I have seen that already contains its central idea. Banaszynski, the Yong
annotator, the Sokol "clue" annotations and Bregman's pivot map all converge on curiosity-driven
ordering.

**MATCH — and this should not be changed.** It is the single most craft-aligned field in the
implementation.

**One asymmetry worth naming.** `why_reader_wants_next` is a justification the architect writes
about its own plan, and a justification can be satisfied by assertion — *"the reader will want
to know what happened next"* passes. The exercise the professionals actually use (exercise 2)
produces a *checkable* pair instead: what the reader now wonders, and what the next beat
delivers. The difference is that a question can be compared against the next beat's content;
a justification cannot.

**Risk:** LOW, and it is a risk of weak signal rather than wrong behaviour.
**Minimal future change:** if anything is added to the architecture on the strength of this
campaign, this is the candidate: a `reader_now_wonders` field per beat, checkable against the
following beat. See §13.
**Confidence:** HIGH on the match; MEDIUM on the value of the addition.

---

## 7. Story Architect — mode and abstraction

**Current behaviour.** A beat has `happens`, `concrete_carrier`, `concept_introduced`,
`must_not_say_yet`, `facts_allowed`. There is no scene/summary/explanation/argument
distinction and no abstraction level.

**Craft evidence.** F-03. The ladder of abstraction is taught as a *pacing instrument*: a
stalled passage is a signal to change rung. The reverse outlines show the movement doing real
work — nine LOW/MID paragraphs in `BR-02` to earn one HIGH sentence; the `BR-14` register
string alternating deliberately. And the two background models (F-23) are literally a choice
about whether explanation is blocked or braided.

**MISMATCH.** The architecture cannot currently notice that six consecutive beats are
explanation, or that it has spent nine paragraphs at HIGH. `concept_introduced` is the closest
field and it marks *where a concept is introduced*, not *what altitude the beat runs at*.

**Risk:** MEDIUM. This is the plausible mechanism behind the owner's "compressed into the
insight" complaint: with no altitude model, nothing prevents an interpretation being attached
to every beat.

**Minimal future change:** none yet. This is the item most likely to become scaffolding — a
LOW/MID/HIGH field that the architect fills in without changing anything. It should only be
added alongside something that *reads* it. **Confidence:** MEDIUM.

---

## 8. Writer packet (`build_packet`, `render`)

**Current behaviour.** 844 words replacing 4,796–5,840. No research pack bodies, no source
roles, no provenance, no `evidence_gaps`. Prohibitions are rendered as imperatives, and a
prohibition phrased as a description of the evidence is refused rather than cleaned.

**Craft evidence.** F-22 is direct vindication, and from the owner's own primary model:
Bregman's Benjamin Lay essay carries 38 footnotes for 5,072 words of prose containing almost
no in-line source machinery. The research is entirely present in authority and entirely absent
from the sentence. The module's doctrine line — *the value of research is not measured by how
much of it appears in the article* — is a correct statement of observed professional practice.

F-16 adds a boundary the packet gets right and the leak-detector overshoots (§9).

**MATCH, strongly. This should not be changed.** The `validate_packet` refusal-not-cleaning
design is also correct: a cleaned prohibition would still carry the sentence shape.

Two smaller observations. `render()` already instructs *"One difficult idea at a time. Give
each paragraph one job."* — which is exercise 1 stated as a rule with no verification anywhere.
And `EXPLAIN AT FIRST USE` for definitions is the right slot for F-02, but "at first use" is
weaker than what Bregman and Scientias independently do, which is to place the explanation
*before* the term.

**Risk:** LOW. **Minimal future change:** none. **Confidence:** HIGH.

---

## 9. Provenance frames and negative claims

**Current behaviour.** `PROVENANCE_FRAMES` bans 22 patterns from the packet, `leaks()` reports
them, `negative_claim_scan` reports 22 negative sentence shapes in the finished article, and
`negative_admission_audit` adjudicates against the ledger.

**Craft evidence.** F-16 splits the target in two, and the split matters:

- **Correctly targeted:** `does not (establish|say|state|tell|report|describe|show|prove)`,
  `nothing in the (source|anchor|evidence)`, `no such claim`, `is not supported by`, source-id
  markers, the role taxonomy, `sha256`, `verified excerpt`. These are all the machine
  describing its own evidence. The craft literature agrees: Banaszynski says you do not show
  proof around background the way you show proof around new information.

- **Broader than the evidence warrants:** the bare phrase `the evidence`. Professional
  annotators praise reader-facing provenance in three separate exemplars — Yong's *"Speaking at
  a press conference today"* (*"important for readers in case they want to track it down"*),
  Qiu's flagging of an unpublished study, and Waldman's fully transparent methodology block
  (*"By giving the reader the opportunity to explore our processes and logic, we build trust"*).

**And one category with no home at all (F-17).** Scientias routinely writes: *"Ook dat cijfer
vraagt om voorzichtigheid: het betekent niet dat deze mensen letterlijk 2,2 jaar langer leven."*
That is a `does not mean` construction, and it is the opposite of the Jia defect. *"The source
does not describe how any visitor perceived these spaces"* is the machine talking about itself.
*"That percentage does not mean these people live 2.2 years longer"* is the world being
clarified, and it prevents a misreading the reader would otherwise make. `negative_claim_scan`
would flag the second alongside the first.

Calibration: published prose contains negative-shape sentences at 0.043 (Bregman) to 0.059
(control) per paragraph. The scanner is correctly a report. **Under no circumstances should it
become a gate.**

**MATCH on the core, MISMATCH at two edges.** **Risk:** LOW for the packet ban (it constrains a
prompt, not prose); LOW-MEDIUM for the scan, and only if anyone tightens it.
**Minimal future change:** none. Document that `does not mean` about the world is a different
category from `does not say` about the evidence, so a future tightening does not erase it.
**Confidence:** HIGH.

---

## 10. Continuity Editor (`continuity.py`)

**Current behaviour.** Owns paragraphing at the last stage. Linguistic freedom, zero factual
freedom. Lineage plus a semantic delta gate. `writtenness()` reports paragraph count,
`solo_ratio`, `solo_texts`, signpost openers, sentence-length median and spread.
`architect_rhetoric` blocks rhetorical micro-direction in the architect's fields.

**Craft evidence — three separate verdicts.**

**(a) Moving paragraphing to the last stage: MATCH.** No craft source addresses this directly,
but it follows from the observation that paragraphing is a pacing decision made over finished
prose, which is what reverse outlining assumes (exercise 1).

**(b) Blocking the architect's rhetorical direction: MATCH, and this is the real fix.** The
0.90–0.93 similarity measurement between architect fields and finished sentences identifies a
transcription channel, and closing it is correct. This is also what actually went wrong in Jia:
the prominent slots were filled with restatements of the scaffold.

**(c) Treating one-sentence paragraphs as the defect: OVER-CORRECTION.** F-14, and the
calibration in §0. The docstring reads: *"A one-sentence paragraph is a slot that FORCES its
sentence to perform."* It does — and forcing a sentence to perform at a hinge is the single
most valuable device in Bregman's repertoire:

> *"The deniers are us." · "But isn't it all a bubble?" · "So. What do we do?" · "Three things,
> at minimum." · "Genes can't be undone. Poverty can." · "It's the context, stupid." · "It's a
> lack of cash."*

Eight percent of Bregman's paragraphs are 15 words or shorter; 19% of those carry a question
mark; they sit at 7%, 31%, 34%, 60%, 71%, 74%, 77% and 78% of one article. This is the
mechanism of the "breathing room" the owner has asked for — not longer explanation, but a hole
cut in the page at the moment the reader needs to catch up.

And `solo_ratio` cannot tell Jia from published work: 0.33 against a published range of
0.00–0.37.

**Risk:** MEDIUM-HIGH, and specific. `writtenness` only *reports*, so nothing is enforced today
— but the field is named for a defect, and a reviewer or a future gate reading
`solo_ratio: 0.33` will drive it down. That would remove the device rather than the defect,
and the result would be flatter prose that scores better.

**(d) One further calibration, now better supported.** `SIGNPOST_SHAPES` flags openers
beginning *read / look at / notice / consider / remember / go back / return*. Bregman opens
paragraphs with *"Look at the first line of this graph"* and *"Remember: the models of today
are the worst models we will ever have."* Those would be flagged.

And so would taught craft. The Open Notebook's *Good Transitions* uses the word **signpost as
praise** — *"The short, declarative sentence that begins the next paragraph acts like a
signpost for readers, signaling in uncomplicated language…"* — and teaches four visible
transition devices: head-to-tail echo, the contrast turn, "But wait", and a dated launch-pad
sentence after a section break. Douglas Fox describes building a *"launch pad"* with an exact
date, time of day and city so the reader lands oriented. Robin Lloyd calls head-to-tail
transitions a deliberate control mechanism used *"more intentionally, more aggressively"* for
clarity.

So the detector is measuring two different things under one name. **Content** transitions point
at the material and are good craft in every form. **Outline** transitions point at the
article's own structure and belong to argument. The detector is still the good one — Jia is at
0.333 per paragraph, 6.6× Bregman and 66× the narrative exemplars — but it needs a **published
baseline and a content/outline split**, not a threshold at zero.

**(f) Section breaks are missing entirely.** *Good Transitions* calls the judicious use of
section breaks *"perhaps the most critical tool for creating transitions in longer stories"*,
and notes that what makes them work is not the break but **the sentences that bracket it**.
Fox uses them deliberately as pacing: *"create a little bit of a speed bump — to jar the reader
just a tiny, tiny bit… The intention of the break is to slow things back down again."* PR #62
has no concept of a section break, and it is a paragraph-level pacing device — Continuity
Editor territory.

**(e) What Continuity does not do: information pacing.** No stage measures facts per sentence,
clause load, or new-concept rate. This is the owner's actual complaint, and there is now a
measurable target: single-clause share 0.55–0.65, commas per sentence below 1.0, ≥4-clause
share below 0.05, sentence-length IQR at least 8 words. `writtenness` already reports
`sentence_len_median` and `sentence_len_spread`, so the module is one small step from
measuring the right thing.

**Minimal future change:** re-baseline or retire `solo_ratio` as a defect signal; keep the
signpost signal and give it a published baseline; consider adding the clause-load diagnostic
next to the sentence-length ones already reported. **Confidence:** HIGH on (b), (c) and (d);
MEDIUM on (e).

---

## 11. Lens realization (`validate_lens_realization`, `lens_is_serialized`)

**Current behaviour.** `IMPLICIT / EXPLICIT / EITHER`. The machine-side lens record is
required; the prose is not required to state it. `lens_is_serialized` reports overlap and is
*"never required and never forbidden"*. The packet says: *"Realise this through the material…
Do not state it as a general principle unless that is genuinely the most natural sentence
available."*

**Craft evidence.** F-10 and F-12. This is **MATCH, and the best-designed contract in the PR.**
Hypothesis H11 is confirmed: nut grafs are usually necessary and sometimes a crutch; the
abstract apex should not be forced; and for contested subjects the teaching pushes the opposite
way and wants the idea stated upfront. A contract that permits both forms, records which was
chosen, and refuses to require either is exactly what the evidence supports.

One check deserves note as well designed: `crip_turn_carrier` must actually appear in the
article, so *something concrete* must be present to carry the turn even when the turn is
implicit. That is F-03 enforced at the only place it can be.

**Risk:** none identified. **Minimal future change:** none. **This should not be changed.**
**Confidence:** HIGH.

---

## 12. CUT enforcement, factual surface, semantic redundancy

**Current behaviour.** `cut_evidence` must be non-empty with reasons from a declared set;
`cut_adherence` checks after writing; `factual_surface_audit` looks for entities, numbers and
sensory words absent from the packet; `semantic_redundancy` and
`validate_ending_does_not_restate` catch propositions restating each other.

**Craft evidence.** F-09 and exercise 13. **MATCH, and unusually well aligned.** Adee's
*"finding good background is like sculpting"*; Sokol's annotator's *"what a science journalist
leaves out is as important as what they leave in"*; Twilley's restraint praised twice; Maxmen
praised for omitting a source's job title. Requiring selection to discard something, with a
declared reason, and then checking adherence, is the craft principle mechanised.

`validate_ending_does_not_restate` is also well supported — the annotators praise endings that
reserve a new piece of information (*"usually a no-no for story craft"*) and criticise endings
that merely land.

One observation on the cut-reason vocabulary: `NAME_OVERLOAD` presumes name density is a
problem. Measured, proper-noun density is essentially identical across all three samples
(96.6 / 97.4 / 75.0 per 1,000 words) — it does not distinguish good prose from bad in this
corpus. The reason may still be right per-article; it is not supported as a general concern.

**Risk:** LOW. **Minimal future change:** none. **Confidence:** HIGH.

---

## 13. What is missing entirely

Ranked by evidential strength. **These are hypotheses about what to test, not a build list.**

1. **The ending upstream test.** F-09, supported by McPhee directly and applied independently
   by a Storygram annotator to a published piece. Two of twelve exemplars are criticised for
   ending one paragraph too late; none for ending too early. Nothing in PR #62 asks whether the
   article was finished before it stopped. Cheapest possible form: report whether deleting the
   final paragraph would remove a concrete referent introduced earlier.

2. **`reader_now_wonders` per beat.** F-01. The architecture already has the idea in
   `why_reader_wants_next`; what it lacks is the *checkable* half. A question can be compared
   against what the next beat delivers; a justification cannot.

3. **An information-pacing diagnostic.** F-07, F-21. The owner's stated complaint, now with a
   target band and with `writtenness` already reporting two adjacent measures.

4. **Form-conditional constraints** on the opening requirement and the signposting signal.
   F-05, F-11, F-13. Note again: the change worth testing is *making two constraints
   conditional*, not *adding a form taxonomy*.

5. **A limitations role.** F-18. Scientias carries uncertainty structurally — five consecutive
   short paragraphs, no hedging adverbs. Crip Minds currently has uncertainty leaking into
   sentences as caveats, which is the defect PR #62 exists to remove; giving it a place to
   stand is a different remedy from forbidding it.

6. **Number handling declared per fact.** F-08. Six-way coding, cheap, and the one move that
   generalises across Bregman, the control exemplars and Scientias alike.

7. **A section-break concept with bracketing sentences.** F-13 revised, §10(f). Named by the
   craft literature as the most critical transition tool in long stories, and it is a pacing
   instrument rather than a typographic one.

8. **A scene-provenance check against the ledger.** F-27. The operational form —
   *a scene may be written when a ledger fact is an observer record of that moment, at the
   granularity being written* — is checkable, and it is a more accurate contract than a blanket
   prohibition on scene. This is the item that would most improve the craft/safety boundary.

9. **The reader's objection as a distinct beat role.** F-24, argument forms only, and absent
   from all twelve control exemplars — so this is the weakest item here.

---

## 14. What should not be changed

Stated explicitly because the campaign's job is partly to protect what is right.

1. **The doctrine and the writer packet.** Directly vindicated by Bregman's own practice (38
   footnotes, no source machinery in the prose). §8.
2. **`lens_realization` as `IMPLICIT / EXPLICIT / EITHER`, reported and never required.** The
   best-designed contract in the PR. §11.
3. **The prohibition-as-imperative rule and refusal rather than cleaning.** §8.
4. **CUT as a required, reasoned, afterwards-verified act.** §12.
5. **`architect_rhetoric` — blocking rhetorical micro-direction in architect fields.** This is
   the actual fix for the Jia defect. §10(b).
6. **`negative_claim_scan` as a report.** Published prose carries these shapes at one sentence
   per seventeen paragraphs. It must not become a gate. §9.
7. **The `crip_turn_carrier` presence check.** §11.
8. **`CARRIERS` permitting object, event, place and process.** §2, F-15.
9. **The four-level separation of architecture / paragraph pacing / sentence rhythm / word
   choice.** The Berkeley reported-narrative syllabus states it directly — *"We'll emphasize
   structure, and on all levels. We'll work on overall story architecture… We will also
   scrutinize the sequencing, shaping, and pacing of paragraphs; sentence construction,
   rhythm, and clarity; word choice; even punctuation."* PR #62's Architect / Writer /
   Continuity staging is that model. This is a stronger endorsement of the PR's shape than
   anything in the first pass, and it arrived from the V1 seed.

---

## 15. The weakest empirical support in the current design

Asked directly by the brief. Answer: **the requirement that openings be concrete**
(`validate_architecture`: *"opening_object_or_event missing -- openings must be concrete"*).

It is a hard gate, it is universal, and its evidential base is a practice that holds in 10 of
12 narrative features, about 5 of 15 Bregman texts, and 11 of 25 Scientias articles — with the
clearest counterexamples being two openings that professional annotators single out for praise.
It is also the constraint that compounds: because it is checked first, it silently forecloses
every non-narrative form before the rest of the architecture is even consulted.

Runner-up: the framing of `solo_ratio` as a defect, which the calibration in §0 shows cannot
distinguish Jia from published work.

---

## 16. Unresolved questions

- Whether a reader-question model can be *verified* rather than merely declared. Every
  confirming source is a human reporting their own reading. Nothing in this campaign shows a
  machine can predict where a reader's question falls.
- Whether the pivot paragraph survives the change of register from Bregman's first-person
  newsletter voice to a third-person Crip Minds persona.
- Whether Crip Minds should publish explanatory pieces at all. §3 identifies a gate that would
  hold Ed Yong's whale article. Whether that is a defect depends on an editorial decision the
  owner has not made, and this campaign should not make it.
- Whether the low-clause-load target is achievable by a generator without producing the flat,
  choppy prose that "short sentences" instructions usually produce. Untested.
- Whether any of this improves output. Nothing here was tested against a generation.


---

## 17. What the V1 seed changed here

Three things, none of which reverse a conclusion.

**Better support for the signpost split (§10(d), §10(f)).** The first pass argued from
measurement alone that signposting is genre-bound. The transitions source — which the V1 pass
had listed and this pass had missed — shows the measurement was counting only one of two kinds.
The recommendation moves from *give the detector a baseline* to *give it a baseline and split
content from outline*, and a missing section-break concept is added.

**A ninth protected item (§14).** The Berkeley syllabus endorses PR #62's stage separation
explicitly and at four levels. Worth protecting precisely because the pressure from this
campaign is all in the direction of adding fields to the Architect.

**A new missing item, now ranked second (§13.8).** F-27's three-tier scene provenance is the
single most useful thing either pass found for reconciling craft with the safety invariants,
because it converts "no invented scenes" into a positive, ledger-checkable permission.

**One thing the seed argued for and the evidence does not.** V1 recommended that production
integration wait until an Article Form Gate exists. Rejected as sequencing: a form field with
no consequences is scaffolding, and the first change the evidence actually supports is the
writtenness re-baseline — the only recommendation in this document measured against PR #62's
own code. Tom French's rule cuts the same way: *"The more complex the material, the simpler the
structure should be."* The pressure on this architecture should be downward.
