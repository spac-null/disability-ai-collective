# V1 → V2 adjudication

Every V1 claim V2 could test, checked against the original source. V1 is a research seed; the
verdicts below are V2's, from the originals.

**Method.** All 48 V1 URLs fetched (45× HTTP 200, 3× 403). For every V1 source V2 actually
uses: URL verified, original inspected, re-coded from scratch, verdict recorded. Where V1 and
V2 sampled the same text independently, the two codings are compared directly.

**Sample overlap.** Bregman 8/12 shared · Scientias **0/20 shared** · craft sources 4/16
shared. The Scientias samples are disjoint, so agreement there is genuine convergence rather
than a shared reading of the same pages.

---

## 1. First-order verification

| check | result |
|---|---|
| URLs resolving | 45 / 48 |
| URLs 403 | 3 — `C03` Harvard, `C10` Poynter *Show and Tell*, `C11` Poynter *Tools of the Writer* |
| V1 titles matching live page | 38 / 48 |
| V1 titles differing | 10 — `B09`, `C02`, and Scientias `S02 S07 S09 S12 S13 S15 S18 S19` |

**On the 10 title mismatches.** For the eight Scientias cases the URL slug supports V1's title
(e.g. `S02`'s slug is `helft-van-de-synapsen-verdwijnt-tijdens-winterslaap…` while the live
title is now *"Waar zit een herinnering? Niet waar we dachten"*). Scientias demonstrably
rotates headlines — V2's own independent sample hit the same thing (`SC-03`'s slug says
`rode-stipjes-in-het-vroege-heelal` and its title says *"Astronomen stapelen 217 Webb-foto's"*).
So these are headline changes, not fabrications. `C10`/`C11` return 403 to us, so V1's
"principles" for them cannot be verified either way and V2 does not use them.

**On `C03` (Harvard).** 403. V1 attributes three principles to it. V2 records it unavailable
and uses none of them. V2's own pass hit the identical wall on two Poynter URLs, so this is a
shared limitation, not a V1 defect.

---

## 2. Adjudication table

### Bregman

| v1 | V1 CLAIM | V2 RESULT | VERDICT | EVIDENCE |
|---|---|---|---|---|
| B01 | Opening is a dated concrete event (Cherokee casino) | Confirmed; V2 codes it `DATED_EVENT + SCENE`, concrete at sentence 1 | **CONFIRM** | Same text is V2's `BR-14`; paragraph map in `NONFICTION_REVERSE_ENGINEERING_V2.md` §1 |
| B01 | Caution: "uses more rhetorical questions/fragments than owner preference" | Confirmed and quantified: `BR-14` has the highest question density in the entire Bregman sample at 9.09 per 1,000 words, against 0.87 for the control exemplars | **CONFIRM** | `CRAFT_METRICS_V2.md` §5–6 |
| B01 | "'mental bandwidth' appears after reader already sees the problem" | Confirmed precisely: term coined at paragraph 28 of 50 (56%), after the overloaded-computer analogy at 27 and after the reader's question at 19 | **CONFIRM** | `BREGMAN_ACCESSIBILITY_PROFILE_V2.md` §6 |
| B02 | "gold coins along the path" — cases spaced through a long argument | Confirmed with positions V1 did not give: 13 homeless men at 7%, Bernard Omondi at 20%, Uganda at 25%, Mincome at 42–55%, closing callback at 96% | **CONFIRM** | Newly fetched for V2; 92 body paragraphs, 5,681 words |
| B02 | Opening: "current crisis preface, then London 2009 experiment" | Substantially right, imprecise on order: deck → author's own publication history (P0) → current crisis (P1) → London at P6/92 | **CONFIRM** (minor imprecision) | as above |
| B03 | Opening is an abstract rhetorical question about who drives progress | Confirmed verbatim: body P1 opens *"Who are the visionaries who drive human progress?"* | **CONFIRM** | `theguardian.com/commentisfree/2017/jul/12/…` |
| B03 | "evidence that 'always open with scene' would be overfitting" | Confirmed, and V2 adopts it as a **new case** in its own tally: F-11 now stands on 4 Bregman abstract openings, not 3 | **CONFIRM** | independently corroborates V2 F-11 |
| B04 | "counterexample to 'never state thesis'" | Confirmed; V2 reached the same verdict independently from the same text (`BR-13`, body P0: *"This piece is about one of the biggest taboos of our times"*) | **CONFIRM** | V2 F-12, reached before V1 was supplied |
| B05 | Opening: "broad political claim, then a Financial Times editorial as concrete artefact" | The FT-editorial-as-artefact reading is right (P4) and useful. The opening is not a broad political claim — P0–P3 are the author deliberating whether a pandemic should be politicised at all | **REVISE** | `thecorrespondent.com/466/…`, 97 paragraphs |
| B05 | "an object/document can carry an intellectual history" | Confirmed, and it strengthens V2 F-15 (carrier need not be a person) | **CONFIRM** | as above |
| B06 | Opening: "abstract human-nature frame → fictional Golding story" | Confirmed; V2 independently coded the same text (`BR-08`) as `CONCEPT`, high abstraction, first concrete referent at sentence 5+ | **CONFIRM** | two independent passes agree |
| B07 | "model for SHORT_FEATURE / reported essay" | Cannot be supported at the depth V1 implies. The page yields 453 words across 9 paragraphs; V2 marks it `PARTIAL`. Structural claims about a truncated extract are not safe | **REVISE** | V2 `BR-15`, availability `PARTIAL` |
| B08 | Opening: "Al Gore scene, 2006" | Not a scene, and not the opening move. P0 is direct address — *"If you're old enough, you may remember this moment."* — then a recalled media event with no place or action | **REVISE** | V2 `BR-02`, paragraph map §2 |
| B08 | "converts abstract capability growth to human time" | Confirmed and it is the best instance in the corpus: 30 seconds → 4 minutes → 40 minutes → 6 hours → 12 hours, one fact per sentence | **CONFIRM** | `BREGMAN_ACCESSIBILITY_PROFILE_V2.md` §8 |
| B09 | Title "Abolish the Tobacco Industry" | Live title is *"How I Finally Woke Up to the Sheer Evil of Big Tobacco"*; slug agrees with the live title | **REVISE** | Substack, retrieved 2026-09-04 |
| B09 | Opening: "scale claim followed by jumbo-jet analogy" | Mis-located. The article opens on a reader question (*"People often ask me why…"*), then runs 8 paragraphs of programme news and a fellowship pitch. The scale claim and jumbo-jet analogy are at P10–P13, **inside an explicitly re-published 2024 essay** (*"today, I want to share an updated version of the essay I wrote in 2024"*) | **REVISE** | V2 `BR-04`, paragraphs 0–13 |
| B09 | "makes enormous statistics concrete before expanding the history" | Correct about the passage, and **V1 found something V2 missed.** V2's pass captured only the cigarette-machine figure; the jumbo-jet passage — a crash headline imagined repeating every half hour, then *"That's how many deaths the tobacco industry causes"* — is the stronger scale translation | **CONFIRM** | now added to V2 F-08 |
| B10 | Opening: "precise dated action scene in a Quaker meeting" | Confirmed; V2 independently coded `BR-01` as `DATED_EVENT + SCENE`, concrete at sentence 1 | **CONFIRM** | two independent passes agree |
| B10 | "scene richness depends on source material; cannot be fabricated" | Confirmed, and V2 can now quantify the apparatus: 38 footnotes for 5,072 words of prose | **CONFIRM** | V2 F-22 |
| B11, B12 | form codings (manifesto / short polemic) | Consistent with V2's independent codings of the same texts (`BR-09` `REPORTED_ESSAY`, `BR-10` `POLEMIC`) | **CONFIRM** | — |

### Scientias — samples are disjoint

| v1 | V1 CLAIM | V2 RESULT | VERDICT | EVIDENCE |
|---|---|---|---|---|
| S01 | "exerkines introduced, then AEA/2-AG/BDNF immediately glossed" | Confirmed exactly. P1: *"zogenoemde exerkines: signaalstoffen die door verschillende weefsels worden afgegeven"* — term and gloss in one sentence. P2 names all three and glosses each immediately. The most precisely correct annotation in V1 | **CONFIRM** | newly fetched; 16 paragraphs, 625 words |
| S13 | "explains why prior studies cannot establish sequence before new design" | Confirmed. P1 gives the prior method (symptom score), P2 gives the two design changes (*"Ze maten de beweging een jaar vóór de uitkomst"*, diagnostic criteria instead of a score) | **CONFIRM** | newly fetched; 17 paragraphs |
| S20 | "defines tipping point in plain Dutch then causal chain ice→sunlight→nitrate→food web" | Confirmed. P0 glosses the term in apposition in its first clause; P1 gives the chain exactly as coded | **CONFIRM** | newly fetched; 16 paragraphs |
| S02 | "defines synapse in ordinary language before structural detail; question emerges from contradiction" | Plausible and consistent with the pattern V2 measured across a disjoint 25-article sample; not re-coded paragraph by paragraph, so recorded as untested rather than confirmed | **UNTESTED** | fetched, 20 paragraphs, 819 words |
| — | Overall: "Scientias is strongest as a complexity-explanation reference, not a macro narrative template" | Confirmed independently on a disjoint 25-article sample, and V2 sharpens it: the macro running order is a formula in 21 of 25 cases, and paragraph uniformity (SD 15.9 vs Bregman's 25.1) is the opposite of what the owner wants | **CONFIRM** | `SCIENTIAS_EXPLANATION_PROFILE_V2.md` §13–14 |
| — | V1 lists no quantitative Scientias measures | V2 supplies them, and one V1-adjacent intuition fails: after removing site boilerplate, Scientias asks **0.91 questions per 1,000 words, median 0.00** — it is not a question-driven publication | **N/A → V2 ADDS** | `CRAFT_METRICS_V2.md` §1 caveat 3 |

### Craft / teaching sources

| v1 | V1 CLAIM | V2 RESULT | VERDICT | EVIDENCE |
|---|---|---|---|---|
| C01 | "separate story architecture, paragraph pacing, sentence rhythm and word choice" | Confirmed, near-verbatim, and **V1 understated it.** The syllabus is a genuine 974-word document by a working magazine writer: *"We'll emphasize structure, and on all levels. We'll work on overall story architecture… We will also scrutinize the sequencing, shaping, and pacing of paragraphs; sentence construction, rhythm, and clarity; word choice; even punctuation."* This is a four-level separation model and it **endorses PR #62's stage separation more directly than anything in V2's own pass** | **CONFIRM** | `journalism.berkeley.edu/course-section/j298-introduction-reported-narrative-2/` |
| C01 | (not claimed by V1) | New: the syllabus names the forms explicitly — *"be it conventional magazine feature, reported essay, essay, profile, review, or investigative piece"* — supporting F-05 from a university course; and lists *"signposts"* as a storytelling element to master, not a defect | **V2 ADDS** | as above |
| C02 | "report for narrative; keep narrative true to reporting" | Confirmed verbatim: *"how to report for narrative; and, crucially, how to keep your narrative true to your reporting"* | **CONFIRM** | 271-word course blurb by Cynthia Gorney |
| C02 | "scene/dialogue/tension/background depend on reporting" | V1 inference. The blurb lists the techniques and separately says report for narrative; the dependency is not stated here. It *is* stated in `C13`, so the claim is true but mis-cited | **REVISE** | as above |
| C04 | "the hardest choice is often which story to tell from a large research pile" | Confirmed verbatim (Blakeslee): *"you have this enormous bolus of information and you could probably write five or six stories, but you're only writing one"* | **CONFIRM** | `theopennotebook.com/2011/09/14/art-of-narrative-structure/` |
| C04 | "structure can be planned or discovered; no single method" | Confirmed by two accomplished writers with opposite methods in the same piece — Aschwanden never outlines, Blakeslee always does and calls not outlining *"the worst advice you can give anybody"* | **CONFIRM** | as above |
| C04 | (not claimed by V1) | New and important: Tom French — *"What you want is for the structure to be as simple as it can be so that the reader has the best chance possible to think about the complexity of what you're trying to get across. The more complex the material, the simpler the structure should be."* This argues against elaborating the Story Architect for hard material | **V2 ADDS** | as above |
| C04 | (not claimed by V1) | New: Blakeslee's "dessert and vegetables" gives the only interval in the whole teaching corpus — *"I'll write eight or nine paragraphs and then I'll go back into something more entertaining to give the reader a rest"* | **V2 ADDS** | as above |
| C05 | "block or braided/zipper; answer reader questions when they arise; introduce jargon slowly" | Confirmed; V2 read the same source independently as `CT-03` and built F-01 and F-23 from it | **CONFIRM** | two independent passes agree |
| C06 | "too much explanation collapses story structure" | Confirmed verbatim, and it is a pull-quote repeated twice: *"If you spend all your time explaining rather than telling a story or advancing an argument, the structure of your writing will collapse under that explanatory weight."* (Carl Zimmer) | **CONFIRM** | `theopennotebook.com/2015/07/07/explaining-complexity/` |
| C06 | "disperse massive explanations or tell the story of how an explanation was discovered" | Confirmed verbatim, and **V2 promotes it to a finding V2 did not have:** *"Tell the story of the explanation, rather than giving the explanation itself."* | **CONFIRM → V2 ADDS** | as above; new F-26 |
| C06 | V1's exercise: "delete explanation until a nonexpert becomes confused; restore only that layer" | Not in the source. The source says find *"the minimum amount of explanation required"* and *"How little explaining can you get away with?"* — a reasonable operationalisation, but V1 presents it as if it were the source's | **REVISE** | as above |
| C07 | "orientation can be explicit without being banal; no single formula" | Confirmed; V2 read this source independently as `CT-11` | **CONFIRM** | two independent passes agree |
| C08 | "transitions should not become afterthoughts" | Confirmed verbatim: *"like any critical piece of engineering, transitions shouldn't be an afterthought"* | **CONFIRM** | `theopennotebook.com/2018/09/25/good-transitions…` |
| C08 | "transition type should follow logical relation" | Confirmed: *"Building successful transitions comes down to knowing with a certain level of granularity what the logical progression of ideas is within the story"* | **CONFIRM** | as above |
| C08 | **"visible formulaic transitions expose scaffolding"** | **The source does not support this as a rule, and it partly contradicts it.** It says transitions *"can easily come across as formulaic, forced, obvious, or patronizing"* — a risk. It then teaches four **visible** devices approvingly: head-to-tail echo, the "contrast approach", the "But wait" approach, and a short declarative signpost. Verbatim: *"The short, declarative sentence that begins the next paragraph acts like a signpost for readers"* — approving. Robin Lloyd calls head-to-tail transitions *"a control mechanism… grabbing the reader and saying, 'Look, we're going to keep talking about this topic'… more intentionally, more aggressively."* Her caution is *use sparingly*, not *delete first* | **REJECT as stated** | as above; see §3 below |
| C08 | V1's exercise: "remove every explicit signpost; add back only where absence causes a real jump" | **Rejected as a general rule** by its own cited source. V2 had the same exercise (exercise 6) and it is now conditioned | **REJECT** | as above |
| C09 | "sometimes the best ending is already a paragraph or two earlier" | Confirmed; V2 built F-09 from the same source independently, tracing it to McPhee | **CONFIRM** | two independent passes agree |
| C10, C11 | Poynter principles (ladder of abstraction; information pacing; gold coins) | Both URLs 403 for V2. V2 does not use them. The ladder principle is independently established from `CT-04`, which quotes Clark directly, so the substance survives the unavailable citation | **UNVERIFIED** | V2 hit the same 403s in its own pass |
| C12 | "scene and summary are different modes; both necessary; reflection is a third mode" | Present in the source, but the source is a **five-week memoir course marketing page** (582 words of week-by-week blurbs), not craft instruction with reasoning, and its domain is memoir rather than reported nonfiction. Accurate paraphrase, much lower evidential weight than "main evidence-backed lesson" implies | **REVISE** | `creativenonfiction.org/syllabus/scene-summary/` |
| C12 | (not claimed by V1) | New concepts worth keeping: *"nano-scenes within summary to keep the storyline vivid"* and *"general time versus specific time"* | **V2 ADDS** | as above |
| C13 | "scenes are reporting products, not prose inventions" | Confirmed verbatim: *"journalists do not fabricate scenes; they report them"* | **CONFIRM** | `niemanstoryboard.org/2023/04/20/…` (Lauren Kessler) |
| C13 | (not claimed by V1) | **The most valuable single omission in V1.** Kessler gives a worked three-tier taxonomy of legitimate scene provenance for one article: (1) direct observation — *"I sat quietly in the corner and took notes"*; (2) **debriefed observer** — a scene that *"reads like the product of direct observation, but was not"*, built from a doctor's second-by-second notes read aloud, plus follow-up questions, prior sight of the room, conversations with the daughter, having met the dog; (3) recorded material — *"after I watched and rewatched the tape"*. Governing rule: *"A scene can be written only if the journalist has the material, however that material is ever-so-carefully gathered."* Tier 2 is the tier Crip Minds actually operates in | **V2 ADDS** | as above; new F-27 |
| C13 | (not claimed by V1) | New: *"The narration… is presented as simply as possible, unadorned by adjectives, adverbs, metaphors… The moments themselves were dramatic; I did not want to force more drama into the retelling."* Independently corroborates the ProPublica annotator's rule, from a second professional | **V2 ADDS** | as above; new F-28 |
| C14 | "reverse engineer strong stories into parts and purposes; different sections use different tools" | Confirmed: *"each is its own part of a bigger story, and each calls on using different tools"* (Jacqui Banaszynski — the same author as V2's `CT-03` background quotes, so V2 now has two independent pieces from one Knight Chair) | **CONFIRM** | `niemanstoryboard.org/2024/04/02/…` |
| C14 | (not claimed by V1) | New: *"We start with a story vision and purpose in mind. Then we have to back up and think about the pieces-parts we need: X sources, Y observation, Z context. From there, we build forward."* Structure drives **acquisition** — the reverse of PR #62's acquire-then-structure order | **V2 ADDS** | as above; new F-29 |
| C15 | "structure follows reporting material and purpose; chronology often best for complicated subject matter" | Confirmed near-verbatim (Sarah Scoles): *"it's good for the reader, if you're writing about complicated things, to go with a chronological structure"* | **CONFIRM** | `niemanstoryboard.org/2026/06/04/…` |
| C15 | (not claimed by V1) | New, and the strongest precedent in the corpus for Crip Minds: Sebastian Junger *"covered events entirely through second-hand accounts and materials"* for a 4,765-word narrative feature. Canonical narrative nonfiction with zero direct observation | **V2 ADDS** | as above; strengthens F-27 |
| C15 | (not claimed by V1) | New **counterexample** to just-in-time glossing: Junger *"includes technical fishing and boat terms with no definitions, because he believes it makes the piece flow but doesn't feel it integral to explain"* | **V2 ADDS** | as above; counterexample added to F-02 |
| C16 | scene/summary/exposition sequencing | Fetched (1,738 words) but not re-coded in this pass; recorded untested | **UNTESTED** | `niemanstoryboard.org/2024/07/25/…` |

### V1's synthesis claims

| V1 CLAIM | V2 RESULT | VERDICT | EVIDENCE |
|---|---|---|---|
| "The craft evidence argues against a single fixed `object → discovery → turn → Crip turn → ending` template" | Confirmed independently and extended: V2 shows the constraint that actually enforces the single template is the hard concrete-opening gate, and that `ARTICLE_TYPES`'s three live values are all narrative | **CONFIRM** | `PR62_CRAFT_GAP_ANALYSIS.md` §4–5 |
| "Bregman's strongest transferable characteristic is not merely 'simple sentences'. It is controlled alternation of cognitive registers" | Half right, and the dichotomy is false. The alternation is real — but the prestige control exemplars alternate too, so alternation does not distinguish him. What distinguishes him is measurable and syntactic: 60% single-clause sentences vs 44%, 0.88 commas per sentence vs 1.35, 6% long sentences vs 17% — at **identical** abstract-noun density (20.3 vs 20.2 per 1,000 words) | **REVISE** | `CRAFT_METRICS_V2.md` §2–3, §5 |
| "explicit thesis is not inherently bad" | Confirmed; V2 reached it independently and added the placement finding: 0–10% or 70–100%, rarely between | **CONFIRM** | V2 F-12 |
| "Report for narrative" as a high-confidence finding | Confirmed and sharpened by `C13`'s three-tier provenance taxonomy, which V1 had the source for but did not extract | **CONFIRM** | V2 F-27 |
| Proposed `ARTICLE_FORM` gate with 7 values | The premise is confirmed; the remedy is revised. Adding a form field changes nothing on its own — a field with no consequences is scaffolding. What the evidence supports is making the two genuinely form-dependent **constraints** conditional: the concrete-opening requirement and the signpost signal | **REVISE** | `PR62_CRAFT_GAP_ANALYSIS.md` §4 |
| Recommendation: "production integration should wait until an Article Form Gate exists conceptually" | Rejected as a sequencing rule. V2's evidence puts a different change first, because it is the only one measured against PR #62's own code: re-baseline the writtenness module. `solo_ratio` cannot distinguish Jia (0.33) from published work (0.00–0.37); the signpost rate can (0.005 → 0.051 → 0.333) | **REJECT** | `PR62_CRAFT_GAP_ANALYSIS.md` §0 |
| "Freeze, do not discard" PR #62 | Confirmed, and V2 adds a protected list of eight things that should not change | **CONFIRM** | `PR62_CRAFT_GAP_ANALYSIS.md` §14 |
| V1 §10: "Not yet claimed: statistically meaningful sentence-length, nominalization or paragraph-function distributions" | Honest and correct. V2 supplies them for 52 texts and 97,187 words, with denominators and limitations | **N/A → V2 ADDS** | `CRAFT_METRICS_V2.md` |

---

## 3. Where V1 changed V2

Three changes, each traced to an original V2 read for itself.

**(a) F-13 on transitions is revised.** V2 had concluded that visible signposting is a genre
marker of the argumentative essay and near-absent from narrative features — measured at 0.051
signposts per paragraph in Bregman against 0.005 in the control exemplars. `C08` shows what
that measurement missed: narrative features *do* use visible transition devices, just not
outline-announcing ones. The distinction is not visible vs invisible. It is:

- **Content transitions** — head-to-tail echo, the contrast turn, "But wait", a dated
  launch-pad sentence after a section break. Visible, taught, praised, used in narrative.
- **Outline transitions** — announcing the structure ("First… Next… Three things, at
  minimum"). Genre-bound to argument.

This *strengthens* the gap analysis rather than weakening it: PR #62's `SIGNPOST_SHAPES` flags
openers beginning *read / look at / notice / consider / remember / go back / return*, and `C08`
teaches precisely that class of short declarative reader-directing sentence as good craft. The
detector still discriminates Jia powerfully; it now clearly needs a baseline rather than a
threshold at zero.

**(b) Scene provenance gets a real taxonomy (new F-27).** V2's F-19 said narrative density is a
function of evidence density. `C13` supplies the operational version: three named tiers of
legitimate scene provenance, worked through one published article, with tier 2 — the debriefed
observer — being the tier Crip Minds actually occupies, since it works from documents that are
themselves observer records. `C15` adds Junger's *The Perfect Storm* as a canonical
zero-observation narrative. The engine-relevant form: **a scene may be written when a ledger
fact is an observer record of that moment, at the granularity being written.**

**(c) "Tell the story of the explanation" becomes a finding (new F-26).** Carl Zimmer's move —
disperse a massive explanation, or narrate how the explanation was discovered instead of
delivering it — is a structural option V2 had not named. It is also, in retrospect, what
`BR-08` and `BR-14` both do.

Two smaller corrections V1 caused: the jumbo-jet scale translation in `BR-04` (V1 mis-located
it but found it; V2 had missed it entirely), and the fact that `BR-04` is a **composite
document** — a newsletter wrapper around a re-published 2024 essay — which V2 had not recorded
as a corpus-composition caveat.

## 4. Where V1 was wrong in a way that matters

- **The transitions principle and its exercise** (`C08`), contradicted by the source cited.
  This is the one V1 claim that, if inherited, would have pushed the engine toward deleting
  taught craft. V2 had the same exercise and has now conditioned it.
- **The `B09` opening**, coded from an embedded essay rather than the article. A reminder that
  Substack pieces are often composites.
- **`C12` treated as evidence.** A course marketing page for a memoir class is a weak citation
  for a claim about nonfiction modes; the claim survives on `C01` and `C16` instead.
- **`B07` structural claims from a 453-word truncated extract.**

## 5. Where V1 was right and V2 had missed it

- `C13`'s scene-provenance taxonomy — the most useful thing in either pass for reconciling
  craft with Crip Minds' safety rules.
- `C06` on explanatory collapse, in Carl Zimmer's own words.
- `C04`'s "the more complex the material, the simpler the structure should be" — which argues
  against the direction PR #62 has been travelling.
- `B03` as a fourth abstract-opening case.
- The jumbo-jet passage in `BR-04`.
- `C01` as an unexpectedly strong endorsement of PR #62's four-level stage separation.

## 6. Independence

V2 stands without these files. The V1 pass and the V2 pass share 8 Bregman texts, **no**
Scientias articles, and 4 craft sources; on the shared Bregman texts the two independent
codings agree on every opening except `B05`, `B08` and `B09`. Every finding V1 prompted is
cited to an original V2 fetched, read and quoted — never to V1's paraphrase — and is flagged
`v1_prompted: true` in `craft_evidence_table_v2.jsonl` so the provenance stays visible.
