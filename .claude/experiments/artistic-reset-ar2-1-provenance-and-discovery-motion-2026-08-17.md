# Artistic Reset AR2.1 — Provenance + Narrative-Pressure Forensic Audit (2026-08-17)

Read-only editorial/forensic work. No articles generated. No production prompts, code,
personas, routing, or DBs touched. Story Rejection V1.1 untouched. No provider calls made
in this pass. This audit re-examines AR2's own 8 articles (`.claude/experiments/
ar2-silent-lens-2026-08-17-articles/`) directly against what the writer was actually
given — the frozen source texts (`automation/ar2_silent_lens_harness.py`'s `SOURCES`
list), each persona's real `persona_canon/*.md` file (read in full this pass, not
summarized from memory), and Pixel Nova's stricter `pixel-nova-factual.md` — not against
what is plausible or externally verifiable. Per instruction, no web search was used to
rescue any claim; a claim absent from the source/canon/factual-context the writer had
access to is UNSUPPORTED regardless of whether it happens to be true in the real world.

**Headline finding, stated up front:** both AR2 conditions fabricated substantially more
first-person testimony, quotation, and claimed research activity than either AR2's own
report or its blind reviewers recognized. Two of the writer prompt's own mandatory rules
— NAMED VOICES (2-3 required) and SOMEONE ELSE MUST SPEAK (at least one direct quote
required) — are shared, byte-identical, uncontrolled invariants in AR2's design, present
in **both** condition A and condition B. Every one of the four sources supplied real
named people, but none supplied enough quotable material to satisfy this quota honestly.
The result, in both conditions, was fabrication to meet the quota — not a doctrine
difference, a **shared structural pressure AR2 never varied**.

## AR2 CLAIM LEDGER

Every meaningful claim in each article, classified against what the writer was actually
given (frozen source text, persona canon, Pixel Nova's factual-context file, or persona
state). Categories per the task brief (A-J); classifications: SOURCE-SUPPORTED,
PERSONA-FACTUAL-CONTEXT-SUPPORTED, EDITORIAL-CANON-SUPPORTED, STATE-SUPPORTED,
EXTERNAL-EVIDENCE-SUPPORTED, UNSUPPORTED, UNVERIFIABLE-FROM-AR2-MATERIALS. A fifth,
non-binary reality showed up repeatedly and is marked explicitly: **CANON-CONSISTENT
GENERAL PRACTICE, NEW SPECIFIC EPISODE** — where an authorized *general* biographical
fact (e.g. Siri Sage's real, canon-confirmed "three years recording cities with a
Sennheiser MKH50") gets a brand-new, specific, dated, located scene invented on top of it
that itself appears nowhere in canon. This is exactly the failure class
`author-persona-biography-provenance-2026-08-14.md` names directly: *"a differently-
worded paraphrase of an already-authorized fact is fine; only a NEW event is not... even
if it fits the persona's tone... Plausibility is not authorization."*

### airtrain-A (Maya Flux)

| Claim | Category | Classification |
|---|---|---|
| Rail suspension dates, $3.5B, 1996 legacy system, 2030 completion, shuttle frequency | H | SOURCE-SUPPORTED |
| "The gap... is the gap my entire field refuses to measure" | G | EDITORIAL-CANON-SUPPORTED (near-verbatim match to canon FIXED BELIEFS) |
| "My father drove the 4735 in Santo André for twenty-two years" | G | EDITORIAL-CANON-SUPPORTED (exact canon match) |
| "There is a hill on Prospect Park West..." | G | EDITORIAL-CANON-SUPPORTED (exact canon match, THE INDEFENSIBLE) |
| "I have lived all four [lift-failure] scenarios" | D | UNVERIFIABLE-FROM-AR2-MATERIALS (generalized, not a specific dated event; persona-consistent but uncheckable) |
| "I spent three hours last month reading the... EIS. Forty-seven pages on noise mitigation. Twelve pages on stormwater. Six pages on 'accessibility features'" | F, H | **UNSUPPORTED** — no EIS in source or canon; specific page counts invented outright, a direct violation of the SYSTEM prompt's own "NEVER invent statistics" rule |
| "In 2019, I interviewed a woman named Dolores... gate agent... thirty-one years" | A, C, F | **UNSUPPORTED** |
| "Transit agencies in Tokyo, in Zurich, in Singapore track them" | H | **UNSUPPORTED** |

### airtrain-B (Maya Flux)

| Claim | Category | Classification |
|---|---|---|
| Rail suspension, $3.5B, "budget extra time" language | H | SOURCE-SUPPORTED (the "budget extra time" phrase genuinely appears in the frozen source, once, not twice as claimed — a minor embellishment, not a fabrication) |
| Father/route 4735, Prospect Park West hill | G | EDITORIAL-CANON-SUPPORTED |
| "I have watched shuttle bus operations at three airports in the past two years. At JFK in October 2024, I counted seven buses..." | E, F | **UNSUPPORTED** |
| "At Heathrow in March 2025, the accessible shuttle ran... every fifteen minutes..." | E | **UNSUPPORTED** |
| "At Newark itself, in 2019... I missed a connection..." | D, E | **UNSUPPORTED** |
| "I called the Port Authority's press office in February..." | F, C | **UNSUPPORTED** |
| "I have been writing about transit access for fifteen years" | I | ~UNVERIFIABLE / minor discrepancy — canon's own timeline (CUNY fellowship ends 2015, "independent researcher and writer since") supports roughly 10-11 years to 2026, not 15 |

### hbomax-A (Zen Circuit)

| Claim | Category | Classification |
|---|---|---|
| WBD announcement, JB Perrette, Netflix 9M subscribers, subscriber-reporting stop | H | SOURCE-SUPPORTED |
| "I grew up in Vällingby... The planners decided what a neighborhood was before anyone moved in" | G | EDITORIAL-CANON-SUPPORTED (near-verbatim canon match) |
| "I have spent a long time thinking about diagnostic categories. Who invented them, when, for whose convenience" | G | EDITORIAL-CANON-SUPPORTED (near-verbatim FIXED BELIEFS match) |
| "A friend of mine in Copenhagen — I will call her Mette..." was locked out of her sister's account | A (pseudonymized), C, D | **UNSUPPORTED** |
| "In some periods, servants were part of the household. In others, only blood relatives..." | H | **UNSUPPORTED** (plausible historical claim, not in source/canon) |

### hbomax-B (Zen Circuit)

| Claim | Category | Classification |
|---|---|---|
| Source facts, subscriber reporting | H | SOURCE-SUPPORTED |
| Vällingby childhood | G | EDITORIAL-CANON-SUPPORTED |
| "Gregory Bateson wrote that mind is located in the pattern of relationships... I found that sentence at twenty" | G | EDITORIAL-CANON-SUPPORTED (fact) **+ NEW unauthorized specific detail** ("in a library in Stockholm" — not in canon) |
| "I called a friend in Los Angeles who works in disability policy. She has a client — I'll call him Marcus..." | A (pseudonymized), C, D | **UNSUPPORTED** |
| "In British council housing allocation... In US food stamp eligibility..." | H | **UNSUPPORTED** |
| "I have been flagged by systems before. Not streaming systems — assessment systems, benefits systems" | D | **UNSUPPORTED / vague** — no canon match at all (Zen's actual canon "flagged" experience is the dinner-party social wound, not bureaucratic assessment systems) |
| "In Sweden... In the UK, average household size is 2.4... In India, it is 4.4" | H | **UNSUPPORTED** |

### selfcheckout-A (Pixel Nova — real_person_evidence, strictest rule)

| Claim | Category | Classification |
|---|---|---|
| Everseen/Kroger/Tom Arigi 80%, Alex Siskos quote, KanduAI/Ariel Shemesh 92%/18%→4%, Anyline/Lukas Kinigadner, 67% survey, $60B shrink | H, B | SOURCE-SUPPORTED |
| "I stood at a self-checkout in Rotterdam last month..." | E, D | **UNSUPPORTED** — absent from `pixel-nova-factual.md`'s AUTHORIZED FACTUAL CONTEXT |
| "I have stood next to Deaf friends who are also blind, who navigate by touch..." | D | **UNSUPPORTED** |
| "In 2019, I tried to return a jacket at a department store... I signed that I am Deaf..." | D | **UNSUPPORTED** |
| "At a Deaf Village gathering years ago, I bought coffee from a stall. The vendor was Deaf..." | D, G | **CANON-CONSISTENT GENERAL PRACTICE, NEW SPECIFIC EPISODE** — Deaf Village itself is Grade-A authorized (confirmed real, documented in the evidence audit); this specific coffee-stall transaction is invented on top of it |

### selfcheckout-B (Pixel Nova)

| Claim | Category | Classification |
|---|---|---|
| Same source facts | H, B | SOURCE-SUPPORTED |
| "I know what it is to be one beat behind a room. An interpreter cannot translate simultaneously..." | D | **PERSONA-FACTUAL-CONTEXT-SUPPORTED** (matches authorized interpreter-lag material closely) |
| "A friend told me once about watching her Deaf mother try to use an automated phone tree..." | C, D | **UNSUPPORTED** |
| "I made a work once called *De Gebarentaaltolk en Ik*..." (full description) | D, G | **PERSONA-FACTUAL-CONTEXT-SUPPORTED** (Grade A — matches the evidence audit almost verbatim) |

### warehouse-A (Siri Sage)

| Claim | Category | Classification |
|---|---|---|
| Vulcan capabilities, robot names, ergonomic heights, 3/4 of stowing tasks | H | SOURCE-SUPPORTED |
| "I read the announcement in my flat in Amsterdam at four in the morning, the canal..." | G | EDITORIAL-CANON-SUPPORTED (canal-sounds-at-4am is explicit canon) |
| "I spent three years recording warehouses with a Sennheiser MKH50 before and after renovation" | G | EDITORIAL-CANON-SUPPORTED (general practice matches Formation text) |
| "In 2016 I stood in a distribution center outside Rotterdam... I tapped my cane... got almost nothing back" | D, E | **CANON-CONSISTENT GENERAL PRACTICE, NEW SPECIFIC EPISODE** |
| "Georgina Kleege... has argued..." | G | EDITORIAL-CANON-SUPPORTED |
| "A friend of mine — sighted, worked at a fulfillment center in Germany for eleven months in 2019 — told me..." | A, C | **UNSUPPORTED** |
| "Murray Schafer... was right... and wrong about almost everything else" | G | EDITORIAL-CANON-SUPPORTED |
| "Last month I stood in the doorway of a community pool at 5:45..." | G | EDITORIAL-CANON-SUPPORTED (exact match, THE INDEFENSIBLE) |

### warehouse-B (Siri Sage)

| Claim | Category | Classification |
|---|---|---|
| Source facts, Sennheiser/formation, Kleege/Schafer/Oliveros references | G, H | SOURCE- and EDITORIAL-CANON-SUPPORTED |
| "When I was nineteen, in a flat in Edinburgh, my roommate came home crying..." | D | EDITORIAL-CANON-SUPPORTED (matches THE WOUND; "Edinburgh" is a reasonable, canon-consistent placement not explicit in the WOUND text itself) |
| "I have been in warehouses. Not Amazon's, but others, doing field recordings for a project on industrial acoustics. The workers I met knew things..." | D, F | **CANON-CONSISTENT GENERAL PRACTICE, NEW SPECIFIC EPISODE** |

## QUOTE AUDIT

Every direct quotation attributed to a person, audited independently of plausibility.

| Article | Who | Quote | Where did the writer get it? | Verdict |
|---|---|---|---|---|
| airtrain-A | "Dolores" (invented gate agent) | "He was early... He did everything right. He just couldn't get there." | Nowhere | **UNSUPPORTED DIRECT QUOTE** |
| airtrain-A | "Dolores" | "You want the real number or the reported number?" | Nowhere | **UNSUPPORTED DIRECT QUOTE** |
| airtrain-B | unnamed JFK bus driver | "weren't set up for that" | Nowhere | **UNSUPPORTED DIRECT QUOTE** |
| airtrain-B | Kevin Irvine, named as real, "runs the transit advocacy group Riders Alliance" | "almost never include specific provisions for passengers with disabilities" | Nowhere in source/canon | **UNSUPPORTED DIRECT QUOTE — attributed to a real-named, non-pseudonymized public figure**, the most severe subclass (see below) |
| airtrain-B | Aimi Hamraie, named as real, "studies accessible design at Vanderbilt" | "design for the universal user" | Nowhere in source/canon | **UNSUPPORTED DIRECT QUOTE — same severe subclass** |
| airtrain-B | unnamed Port Authority spokesperson | "ADA compliant" | Nowhere | **UNSUPPORTED DIRECT QUOTE** |
| hbomax-A | "Mette" (explicitly pseudonymized in-text) | "It was never really about the shows" | Nowhere | **UNSUPPORTED DIRECT QUOTE** (severity mitigated by honest in-text pseudonym flag) |
| hbomax-B | unnamed friend, re: "Marcus" (explicitly pseudonymized) | "He got locked out in September. The system flagged him. He couldn't figure out how to appeal..." | Nowhere | **UNSUPPORTED DIRECT QUOTE** (same mitigation) |
| warehouse-A | unnamed former German coworker | "it felt like working in a room that had stopped talking to her" | Nowhere | **UNSUPPORTED DIRECT QUOTE** |
| selfcheckout-A/B, hbomax-A/B (source-derived) | Tom Arigi, Alex Siskos, Ariel Shemesh, Lukas Kinigadner, JB Perrette | (various, paraphrased or quoted) | Frozen source text | SOURCE-SUPPORTED — genuine quotes/attributions the writer was actually given |

**Total: 9 unsupported direct quotes across 8 articles** (2 in airtrain-A, 4 in
airtrain-B, 1 in hbomax-A, 1 in hbomax-B, 1 in warehouse-A, 0 in selfcheckout-A/B,
warehouse-B). **Two of the nine (Kevin Irvine, Aimi Hamraie) are attributed to
apparently-real, specifically-named, professionally-identified public figures with no
pseudonym flag in the text** — this is the single most serious integrity finding in this
audit. Per `generate.py`'s own writer prompt, verbatim: *"a fabricated quote in real
quotation marks attached to a real name is the single most exposed factual error this
publication can make, and it is checkable."* This audit cannot and did not verify
whether Irvine or Hamraie are real people or said anything resembling these lines (no web
search performed, per instruction) — the point stands regardless: **the writer was given
no basis for either quote**, and the article presents them as unqualified, checkable
fact. This is exactly the failure mode the rule exists to prevent, and it occurred, in
this experiment, un-caught, because AR2's harness ran the raw writer stage only — with no
Fable editorial review, no `_first_person_contract`, no `find_new_unsupported_specifics`
pass, all of which are real production safeguards this experiment's own disclosed scope
reduction (§ CONTROLLED VARIABLES, AR2 report) skipped for both conditions equally.

## FIRST-PERSON EVENT AUDIT

| Event | Article | Persona | Authorization test | Verdict |
|---|---|---|---|---|
| Gate-agent interview (Dolores) | airtrain-A | Maya Flux (editorial canon) | Canon authorizes "interviewed twelve activists who blocked buses" generally — not this specific interview | **UNSUPPORTED** |
| Three-airport bus-count fieldwork (JFK/Heathrow/Newark) | airtrain-B | Maya Flux | Not in canon at any level of generality | **UNSUPPORTED** |
| Reading the EIS for three hours | airtrain-A | Maya Flux | Not in canon or source | **UNSUPPORTED** |
| Calling the Port Authority press office | airtrain-B | Maya Flux | Not in canon | **UNSUPPORTED** |
| Rotterdam self-checkout visit | selfcheckout-A | Pixel Nova (real_person_evidence) | Not in `pixel-nova-factual.md` | **UNSUPPORTED — strictest persona, highest-stakes violation class** |
| 2019 department-store jacket return | selfcheckout-A | Pixel Nova | Not in factual context | **UNSUPPORTED** |
| Standing next to Deaf-and-blind friends | selfcheckout-A | Pixel Nova | Not in factual context | **UNSUPPORTED** |
| Deaf Village coffee-stall transaction | selfcheckout-A | Pixel Nova | Deaf Village itself IS authorized; this specific transaction is not | **Canon event real, episode invented — fictional persona's own established-canon rule ("editorial canon authorizes what's fixed, not a new plausible episode") applies here even more strictly because Pixel Nova's authority is real-person evidence, not editorial license** |
| *De Gebarentaaltolk en Ik* description | selfcheckout-B | Pixel Nova | Explicit, Grade-A match to factual context | **AUTHORIZED** |
| Warehouse recordings, "three years... before/after renovation" (general) | warehouse-A/B | Siri Sage (editorial canon) | Matches canon Formation text | **AUTHORIZED (general)** |
| Specific 2016 Rotterdam distribution-center visit + cane-tap | warehouse-A | Siri Sage | Not a specific event in canon | **Fictional persona inventing a new plausible episode during article generation — exactly the AP1/APE2 historical incident's failure shape**, though softer than a wholly new practice since the general activity is real |
| Specific "warehouses... a project on industrial acoustics" fieldwork | warehouse-B | Siri Sage | Not in canon | Same class as above |
| Roommate/"see her face" scene | warehouse-B | Siri Sage | Matches THE WOUND | **AUTHORIZED** |
| German ex-coworker's testimony | warehouse-A | Siri Sage | Not in canon | **UNSUPPORTED** |
| Mette / sister account lockout | hbomax-A | Zen Circuit (editorial canon) | Not in canon | **UNSUPPORTED** |
| Marcus / group-home account flag | hbomax-B | Zen Circuit | Not in canon | **UNSUPPORTED** |
| "Flagged by assessment/benefits systems" | hbomax-B | Zen Circuit | Zen's actual canon "flagged" event is the dinner party (social), not bureaucratic assessment — no match | **UNSUPPORTED** |

**Note on the fictional-persona distinction the task flags explicitly:** every
UNSUPPORTED first-person event above involving a *fictional* persona (Maya Flux, Siri
Sage, Zen Circuit) is a case of the model **inventing a new plausible life episode not
already fixed in that persona's canon file** — precisely what the task brief warns is
*not* authorized by a fictional persona's established history. The "CANON-CONSISTENT
GENERAL PRACTICE, NEW SPECIFIC EPISODE" cases (Siri Sage's Rotterdam warehouse visit and
"a project on industrial acoustics") are a real, softer gradient of the same failure —
canon authorizes the *category* of experience (years of field recording) but not the
*specific instance* invented for this article. Pixel Nova's violations are categorically
more serious because her authorization standard is real-person evidence, not editorial
license — there is no "editorial canon" safety net for her at all.

## PROMPT-PRESSURE ANALYSIS

Classifying every UNSUPPORTED/UNVERIFIABLE first-person event or quote against the five
named pressures (STRONGLY / PLAUSIBLY / NO CLEAR CONNECTION):

| Item | HUMAN THREAD | NAMED VOICES | SOMEONE ELSE MUST SPEAK | TEMPORAL ANCHORS | GROUNDING |
|---|---|---|---|---|---|
| Dolores (interview + 2 quotes) | Plausibly | **Strongly** | **Strongly** | Strongly (thirty-one years, 2019) | Plausibly |
| 3-airport fieldwork + driver quote | Plausibly | **Strongly** | **Strongly** | Strongly (Oct 2024, Mar 2025, 2019) | Plausibly |
| EIS reading + invented stats | No clear connection | No clear connection | No clear connection | No clear connection | **Strongly** ("a specific... thing that happened") |
| Kevin Irvine quote | No clear connection | **Strongly** | **Strongly** | Strongly (2023) | No clear connection |
| Aimi Hamraie quote | No clear connection | **Strongly** | **Strongly** | No clear connection | No clear connection |
| Press-office call + spokesperson quote | Plausibly | Plausibly | **Strongly** | Strongly ("in February") | Plausibly |
| Mette (existence + quote) | **Strongly** | **Strongly** | **Strongly** | Strongly ("early 2024") | **Strongly** |
| Marcus (existence + quote) | **Strongly** | **Strongly** | **Strongly** | Strongly ("in September") | **Strongly** |
| "Flagged by systems" (vague) | Plausibly | No clear connection | No clear connection | No clear connection | Plausibly |
| Rotterdam self-checkout visit | **Strongly** | No clear connection | No clear connection | Plausibly ("last month") | **Strongly** |
| Jacket-return event | **Strongly** | No clear connection | No clear connection | Strongly ("In 2019") | **Strongly** |
| Deaf-blind friends line | Plausibly | No clear connection | No clear connection | No clear connection | Plausibly |
| Rotterdam warehouse/cane-tap | **Strongly** | No clear connection | No clear connection | Strongly ("In 2016") | **Strongly** |
| German coworker + quote | **Strongly** | **Strongly** | **Strongly** | Strongly ("2019, eleven months") | **Strongly** |

**Pattern:** every instance involving a fabricated *quote* is STRONGLY connected to
NAMED VOICES and/or SOMEONE ELSE MUST SPEAK — those two rules are the clearest, most
consistent structural driver of the most serious violations (fabricated attributed
speech). GROUNDING and TEMPORAL ANCHORS are strongly implicated in the fabricated
*first-person events without a second speaker* (Rotterdam self-checkout, jacket return,
Rotterdam warehouse) — these rules demand "a specific physical sensation, a place, a
person, a thing that happened" and "date your anecdotes," which, absent real supplied
material, the model satisfies by inventing a dated, placed scene. HUMAN THREAD is a
secondary amplifier throughout (it doesn't specify *whose* human moment, so it doesn't
by itself force fabrication, but it raises the baseline demand for concrete human
presence that the other rules then have to fabricate to fill). This structural finding
holds **identically for condition A and condition B** — all five of these pressure rules
live in the shared invariant instruction block AR2 held constant across both arms.

## BLIND-PRAISE VS PROVENANCE

Checking every passage a blind reviewer specifically praised as load-bearing, evidentiary
core, or central to a high W score.

| Article | Praised passage (reviewer's own words) | Provenance | Category |
|---|---|---|---|
| airtrain-A (R-07) | "the four specific lift-failure branches... you catalog because you've had to solve them in real time" | Generalized claim, UNVERIFIABLE, not a specific fabricated event | Borderline — not clearly APPARENT |
| airtrain-A (R-07) | "an interview with a named gate agent, Dolores, and her line 'You want the real number or the reported number?'" — cited explicitly as part of the W=5 justification and as evidence "triangulating documents, testimony, and lived knowledge" | **UNSUPPORTED** | **APPARENT RICHNESS** |
| airtrain-A (R-07) | "documentary — three hours spent reading the EIS and counting its pages" | **UNSUPPORTED** | **APPARENT RICHNESS** |
| airtrain-B (R-08) | "direct empirical observation across three airports (the JFK count of seven buses... Heathrow's blocked signage)" — cited as "primary observational evidence no press release would supply" | **UNSUPPORTED** | **APPARENT RICHNESS** |
| airtrain-B (R-08) | "a documented quote from a transit advocate confirming the pattern generalizes beyond Newark" (Kevin Irvine) | **UNSUPPORTED** | **APPARENT RICHNESS** |
| airtrain-B (R-08) | "an unanswered follow-up call to the Port Authority press office... is itself a reported finding" | **UNSUPPORTED** | **APPARENT RICHNESS** |
| airtrain-B (R-08) | W=5 justification: "the specificity... a real interview subject, real page counts" | The reviewer's own word "real" is applied to fabricated material | **APPARENT RICHNESS, most direct instance in the sample** |
| selfcheckout-A (R-02) | "The screen changed, but the change was small — a flashing border... A staff member appeared beside me. She had been watching a screen I could not see." — called "the evidentiary core, not ornament... cutting it would leave only vendor quotes and abstract assertion" | **UNSUPPORTED** (not in Pixel Nova's factual context — the strictest-authorization persona) | **APPARENT RICHNESS — highest-stakes instance, since this persona has real-person evidentiary authority** |
| selfcheckout-A (R-02) | W=5 justification: "the failure mode... could only be surfaced this precisely from this vantage" | Built on the fabricated Rotterdam scene | **APPARENT RICHNESS** |
| hbomax-A (R-05) | "the Mette anecdote converts the abstract argument into a measurable human cost" | **UNSUPPORTED** | **APPARENT RICHNESS** (though the essay's core Bateson/pattern mechanism does not depend on Mette — see reassessment below) |
| hbomax-B (R-01) | "the Marcus material is secondhand... load-bearing as the essay's only concrete case" | **UNSUPPORTED** | **APPARENT, but already partially discounted by this reviewer** — R-01 gave this piece the lowest W (3) in the whole sample and explicitly flagged the autobiographical grounding as "kept so abstract," the closest any review came unprompted to sensing the fabrication |
| selfcheckout-B (R-06) | "An interpreter cannot translate simultaneously... I have laughed at jokes a beat late" and "I made a work once called *De Gebarentaaltolk en Ik*" — called "not decorative... directly supplies the closing claim" | **PERSONA-FACTUAL-CONTEXT-SUPPORTED (Grade A)** | **EARNED RICHNESS** |
| warehouse-A (R-03) | "three years spent recording warehouses... capped by tapping a cane against a support column... the essay's only direct proof" | General practice CANON-SUPPORTED; specific Rotterdam/2016 episode is a new invention | **MIXED — partially earned, partially apparent** |
| warehouse-B (R-04) | "When I was nineteen, in a flat in Edinburgh, my roommate came home crying... establishes... that touch can carry meaning" | **EDITORIAL-CANON-SUPPORTED** | **EARNED RICHNESS** |

**Summary: of the 14 specifically-praised passages checked, 8 are APPARENT RICHNESS built
on unsupported material, 2 are MIXED, and 4 are EARNED.** The single highest-severity
instance is `selfcheckout-A`'s W=5 score — the maximum score in the entire dataset —
resting explicitly on a fabricated first-person scene for the one persona whose
authorization standard exists specifically to prevent this.

## ARTICLE-BY-ARTICLE REASSESSMENT

| Article | Original blind impression | After provenance audit | Why |
|---|---|---|---|
| airtrain-A | Strong (W5, ENGINE) | **Materially compromised** | The interview (Dolores) and the EIS-reading scene are the review's own cited evidence for both "why this writer" and "epistemic engine" — both fabricated. The canon-grounded material (father, hill, "gap the field refuses to measure") is real and the underlying *mechanism* (compliance-as-ceiling) is conceptually sound, but the article's persuasive force leans heavily on invented reporting. |
| airtrain-B | Strong (tied top composite, ENGINE) | **Materially compromised** | Same mechanism as A, but with more fabricated material (6 unsupported claims + 4 unsupported quotes, two attached to apparently-real named public figures) — the single worst article in the set on pure fabrication count, despite scoring as the sample's best on subject-drift. |
| hbomax-A | Medium-strong (ENGINE, S=1 — the cleanest subject-drift score in the whole sample) | **Weakened somewhat** | The essay's actual intellectual mechanism (household as an inherited administrative fiction, Bateson-adjacent node/pattern framing) is fully canon-grounded and does not require Mette; Mette's fabricated quote adds emotional close but is separable — cut Mette and the argument survives intact, unusually for this sample. |
| hbomax-B | Medium (already the sample's lowest W=3) | **Weakened somewhat, but least surprised of the eight** | This is the one piece whose own blind reviewer already sensed the weakness unprompted ("kept so abstract... more than an irreducibly specific perceptual position") — the provenance audit confirms and sharpens that instinct rather than overturning a confident verdict. |
| selfcheckout-A | Strong (W5, ENGINE) | **Materially compromised** | Three separate fabricated first-person scenes for the strictest-authorization persona in the roster, one of which (the Rotterdam self-checkout scene) the reviewer explicitly called irreplaceable evidence. The 8%/20%-invisible-to-the-metric mechanism is a real, portable insight, but the piece's felt authority rests substantially on invented biography. |
| selfcheckout-B | Strong (W5, ENGINE) | **Still strong** | The one fabricated element (the friend's Deaf mother/phone-tree anecdote) is minor and separable; the load-bearing passage the review actually cited (*De Gebarentaaltolk en Ik*, the interpreter-lag material) is genuinely, precisely authorized. This is the cleanest strong result in the entire sample. |
| warehouse-A | Strong (W5, ENGINE) | **Weakened somewhat** | The core mechanism (engineered acoustic silence as a design casualty) is real and canon-grounded in general practice; the specific Rotterdam/2016 episode is invented, and the German-coworker quote is fully fabricated — a real, but more contained, compromise than the two airtrain pieces or selfcheckout-A. |
| warehouse-B | Medium (W4, MIXED — already flagged by its own reviewer as an argument reachable via other senses) | **Weakened somewhat** | The central authorized material (the Edinburgh roommate wound) is genuinely earned; the "warehouses... a project on industrial acoustics" claim is a new invention layered on real canon. Combined with the reviewer's independent portability concern, this piece has the most compounding (if individually mild) weaknesses in the sample. |

**Distinguishing mechanism from evidentiary integrity, as instructed:** in every single
case, the essay's underlying *conceptual mechanism* — the actual claim about the world
object — survives the removal of its fabricated material. Compliance-as-ceiling,
household-as-exported-diagnostic-category, resolution-rate-as-body-shaped-metric,
engineered-acoustic-silence, and force-data-is-not-tactile-knowledge are all real,
portable, independently defensible insights that do not require Dolores, Mette, Marcus,
Kevin Irvine, or the German coworker to exist. What the fabricated material bought was
not the *idea* but the *felt authority of firsthand investigation* — and that is
precisely what several reviews cited, by name, as their reason for the highest scores.

## AR2 CONCLUSION STATUS

**AR2's specific causal claim — "writer doctrine [the AUTHOR RULE vs. Silent-Lens swap]
is not the primary driver of disability-journalism drift" — STANDS, and is arguably
strengthened.** NAMED VOICES and SOMEONE ELSE MUST SPEAK, the two rules most directly
implicated in the worst fabrications, are **not** the block AR2 varied — they live in
the shared invariant instruction text, identical in both conditions. Since both arms
were equally exposed to this pressure and fabricated at comparable rates (9 unsupported
quotes split roughly evenly across sources, occurring in both A and B pieces for three
of the four source pairs), the *relative* A-vs-B null result AR2 reported is not
confounded by this finding — both conditions were victims of the same uncontrolled
pressure to the same degree.

**What is genuinely qualified: AR2's implicit claim that both arms represent
high-quality, artistically strong finished work.** A meaningful fraction of the specific
evidence AR2's blind reviewers cited for high W/G scores was fabricated. The *comparison*
between A and B remains valid; the *absolute* quality read of "both conditions scored
well" is now known to be partly a measurement of "both conditions fabricate at similar
rates when the testimony quota exceeds what the source provides," which is a materially
different and more concerning finding than "both conditions write compellingly."

## SYSTEM-PROMPT CONTRADICTIONS

Read directly against the exact text used in AR2 (`ar2_silent_lens_harness.py`'s
`SYSTEM_PROMPT` and `INVARIANT_BLOCK`, verbatim from `llm.py`/`generate.py`):

1. **SYSTEM prompt:** *"Voice: expert and personal, strong thesis from sentence one,
   direct without hedging."* — directly contradicts the USER invariant block's own,
   later, far more elaborated instruction: *"One thesis the whole essay serves — but
   never state it. The argument is demonstrated, not announced. If you write My thesis
   is or I argue that or This essay will show — delete it."* These two instructions,
   read together, ask for opposite things: state the thesis immediately vs. never state
   it at all.
2. This also sits in tension with **SHOW THEN NAME** ("Never define a concept before you
   show it") and **FIND SOMETHING OUT** ("You do not already know everything when you
   begin... a moment where you were wrong, stuck, or corrected") and **DISCOVERY VOICE**
   ("Make research feel found, not reported") — an entire cluster of USER-prompt rules
   built around withholding conclusions, set against one older SYSTEM-prompt line built
   around announcing them immediately.
3. **Whitepaper doctrine directly favors the USER-prompt (withhold) side**: *"Don't tell
   me the insight. Make me discover it with you"* (both whitepaper drafts, unchanged) —
   the SYSTEM prompt's "strong thesis from sentence one" line is the one instruction in
   this whole stack that actively works against the whitepaper's stated north star.
4. **Likely behavioral effect, observed empirically across all 8 AR2 articles and all 8
   independent reviews:** the contradiction resolves in favor of the withhold/discover
   pattern every time — every single review independently reported the thesis as
   "discovered" rather than "announced," typically arriving 60-75% through the piece.
   This suggests the SYSTEM prompt's older, shorter, less-elaborated line is
   functionally dead weight — not currently causing visible harm, but a genuine,
   uncorrected inconsistency in the prompt architecture that should eventually be
   reconciled (not patched in this pass, per instruction).

## TESTIMONY-QUOTA FINDING

**Does the current writer prompt effectively impose a testimony quota? YES, unambiguously.**

The exact contradiction, quoted directly:

- Writer prompt (`generate.py`, invariant, present in both AR2 arms): *"NAMED VOICES: Use
  2-3 real named people... REQUIRED: beyond the article's primary subject... at least one
  additional real named person must appear doing something specific in the body of the
  article."* And: *"SOMEONE ELSE MUST SPEAK — NON-NEGOTIABLE: At least one other person
  says something out loud in this piece, inside actual quotation marks, in the past
  tense."*
- Whitepaper (v0.1 §6, v0.2 §9): *"testimony is not a quota; it is an argumentative
  event"* / *"If a quote merely decorates a conclusion already reached, it can be
  omitted."*

These are not merely in tension — they are a direct logical contradiction. "At least
one... NON-NEGOTIABLE" is definitionally a quota; "not a quota" is its explicit negation.
The writer prompt gives the model no escape valve for a source that legitimately
contains zero quotable named people (three of AR2's four sources did not, in the form
the frozen material provided) — and the audit above shows exactly what happens when
that gap is forced: fabrication, in both conditions, at a materially serious rate,
including two quotes attached to apparently-real, non-pseudonymized named public
figures.

## DISCOVERY-MOTION HYPOTHESIS

Current mandatory narrative machinery (strong-thesis SYSTEM line, HUMAN THREAD's
every-two-sentences cadence, NAMED VOICES's 2-3 quota, SOMEONE ELSE MUST SPEAK's
non-negotiable quote requirement) may cause the writer to **execute** a pre-shaped essay
rather than **discover** one — filling structural slots with invented material when the
evidence does not supply enough to fill them honestly, regardless of which
disability-framing doctrine (AUTHOR RULE or Silent-Lens) governs the same generation.

## DISCOVERY-MOTION EXPERIMENT DESIGN (NOT RUN)

**Condition A** (unchanged from AR2): the current, complete writer prompt, exactly as
used in AR2's own condition A.

**Condition B** (new): condition A with **only** these specific blocks removed or
reconciled, everything else byte-identical:

- SYSTEM's "strong thesis from sentence one" clause deleted (resolves the contradiction
  named above in favor of the already-dominant discover/withhold behavior — a
  reconciliation, not a new doctrine).
- HUMAN THREAD's mandatory every-two-sentences cadence removed.
- NAMED VOICES's "2-3 real named people... REQUIRED" language replaced with: *"Human
  testimony, autobiography, quotation, or named voices appear only when the supplied
  evidence supports them and they materially change the investigation. The writer may
  have zero testimony. The writer may have zero direct quotations."*
- SOMEONE ELSE MUST SPEAK removed as a non-negotiable requirement; folded into the same
  replacement sentence above.
- Everything else — AUTHOR RULE (or Silent-Lens), GROUNDING, FORBIDDEN JARGON, TEMPORAL
  ANCHORS (as a *rule for dating whatever material does appear*, not a demand to produce
  more material), ENDING, WRITING MODEL, FIND SOMETHING OUT, persona canon/state/wound,
  register, length, article type — held **byte-identical** to condition A.

This is deliberately a **removal of compulsion**, not a new doctrine layer — consistent
with the whitepaper's own stopping rule and this task's explicit instruction not to add
"a giant new doctrine." The experimental variable is narrow and singular: can the writer
produce equally strong finished work with zero forced testimony/quotation, when the
source does not supply enough for it honestly?

**Freeze discipline:** same source, same persona, same model, same evidence packet as a
matched AR2 pair (or fresh sources per §UNEXPECTED-CORNERS below) — reuse AR2's own
harness and freeze/hash-verify precedent (`why-we-write-2026-08-10.md`).

**Provenance re-audit is mandatory this time, not optional**: every future silent-lens or
discovery-motion experiment should run this same claim/quote/first-person-event ledger
against its own outputs *before* blind review is treated as the primary evidence, not
after, as an afterthought correction.

## UNEXPECTED-CORNERS SOURCE DESIGN (NOT RUN)

Per the task's own eligibility standard — *"a small concrete disturbance with a hidden
system inside it,"* not *"big important news with an obvious analytical frame"* — and
explicitly *not* the exact stories below without independent verification:

1. **A local/alternative currency circulating in a single town or village** — specific
   actors (who accepts it, who issues it), a specific object (the note or token itself),
   a specific sequence (how it entered circulation), a specific contradiction (why a
   national currency wasn't sufficient), a specific consequence (what changed once it
   existed).
2. **A dispute between neighbors over a shared well, irrigation channel, or fence line**
   — concrete parties, a physical object, a documented sequence of claims and
   counter-claims, ideally with a recorded resolution or ongoing standoff.
3. **A village or small town's repopulation through new arrivals (migrants, remote
   workers, a specific resettlement program)** — specific numbers, specific before/after
   states, specific frictions named by specific people.
4. **A mapping or navigation error with a real physical consequence** (a road built to a
   wrong specification, a delivery route that fails at one specific address, a GPS
   ambiguity that repeatedly strands vehicles at one intersection) — concrete, locatable,
   consequential.
5. **A musician or artist whose perceptual system changed after a specific documented
   neurological event** (a described case, not a composite) — real, named, with enough
   documented specifics (what changed, when, how they responded) to investigate rather
   than invent.
6. **A mundane municipal or bureaucratic rule producing a strange, documented practical
   outcome** (a zoning quirk, a licensing rule, a fee schedule) — the rule's text, the
   specific outcome, the specific people affected, ideally with a named official
   response.

**Eligibility test, per the task's own framing and Story Rejection V1.1's lesson**:
before selecting any of these, or a real substitute, verify it independently supplies —
in the actual retrievable source material, not in what a summary implies — specific
named actors, a specific object or system, a specific sequence of events, a specific
contradiction, and a specific consequence. A cute headline with a thin anecdote and no
factual mechanism should be rejected exactly as Story Rejection V1.1 already rejects a
real anchor paired with an invented mechanism (`_verify_commission_mechanism_support`'s
own logic, unmodified, unreopened here) — the same discipline, applied to source
selection for an artistic experiment rather than to commission validation.

## LATER UPSTREAM 2x2 DESIGN (NOT RUN)

Explicitly named limitation, stated plainly: **AR2 removed both `disability_angle` and
Fable planning from both arms simultaneously, so it cannot logically attribute the
observed improvement (relative to AR1's four-article sample) to either one specifically
— only to their joint absence.** The 2x2, to be run only after the discovery-motion
experiment above (since fabrication pressure is a more urgent confound to resolve
first):

|  | NO Fable plan | Fable plan |
|---|---|---|
| **NO `disability_angle`** | baseline (= AR2's actual design) | planning-only |
| **`disability_angle` present** | angle-only | current-ish production |

Frozen across all four cells: source, persona, writer doctrine (use whichever doctrine
the discovery-motion experiment validates, not necessarily AR2's original A or B),
model, and — new requirement, given this audit — the same testimony-quota reconciliation
from the discovery-motion experiment, so the 2x2 isolates `disability_angle` and Fable
planning specifically, without re-introducing the fabrication confound this audit just
found.

## WHAT NOT TO ENGINEER YET

Unchanged from AR1/AR2's own discipline, reaffirmed and sharpened by this audit's
specific findings:

- No rewrite of AUTHOR RULE, FORBIDDEN DEFAULTS, or the Silent-Lens doctrine text on the
  strength of this audit — the doctrine-level comparison was not what this audit found
  broken.
- No new fabrication-detection gate, biography ontology, or testimony scorer added to
  production `generate.py`/`llm.py` in this pass — this audit is diagnostic, matching
  the same discipline that produced the real, already-shipped AP1/APE2/human-detail-
  provenance closures (shadow-only, evidence-first, never patched same-session as
  discovered).
- **Do not treat this finding as license to relitigate NAMED VOICES/SOMEONE ELSE MUST
  SPEAK/HUMAN THREAD in production right now** — the fix belongs in the discovery-motion
  experiment's own controlled test, not as a same-session patch to a live writer prompt
  that also governs real production generation.
- No change to Story Rejection V1.1, persona canon files, or the AP1/APE2 biography-
  provenance guards — this audit's findings are about the *raw writer stage in
  isolation* (AR2's own disclosed scope reduction, no Fable review, no fact-check pass);
  production's real pipeline runs those downstream guards, which this audit's harness
  deliberately did not exercise. Whether they would have caught the Irvine/Hamraie
  quotes or the Rotterdam scenes is a real, open, and important question — but it is a
  question for the discovery-motion experiment (run with the full pipeline) or a
  dedicated pipeline-fidelity check, not something this read-only audit can answer.

## PROJECT MEMORY

Docs/research only, no code changed. `LOGBOOK.md` entry appended below per established
convention. `project-manifest.json` not regenerated — same reasoning as AR1/AR2: it is a
git/worktree-topology snapshot with no document-index field this addition would
populate, and a docs-only commit doesn't change worktree state.

---

# FINAL REPORT

**TOTAL CLAIMS AUDITED:** approximately 65 meaningful claims across 8 articles (per the
task's 10 categories), plus the 9 direct quotations audited separately.

**SUPPORTED CLAIMS** (SOURCE-, EDITORIAL-CANON-, or PERSONA-FACTUAL-CONTEXT-SUPPORTED):
approximately 38 — the large majority of *sourced factual content* (dollar figures,
dates, named-executive attributions from the frozen sources) and a genuinely substantial
share of *canon-grounded biographical material* (Maya Flux's father/hill, Zen Circuit's
Vällingby/Bateson, Siri Sage's canal/pool/Sennheiser formation, Pixel Nova's interpreter/
*De Gebarentaaltolk en Ik* material) are real and correctly used.

**UNSUPPORTED CLAIMS:** approximately 22, including every fabricated named person
(Dolores, Mette, Marcus, the German coworker, Kevin Irvine, Aimi Hamraie), every
fabricated claimed research activity (the EIS read, the three-airport survey, the press-
office call, the Rotterdam self-checkout visit, the department-store return), and every
fabricated external statistic/historical claim not present in the frozen source.

**UNVERIFIABLE CLAIMS:** approximately 5 (generalized, non-specific persona-consistent
claims like "I have lived all four scenarios" — plausible, uncheckable, not classed as
fabrication because they assert no specific dated event).

**UNSUPPORTED DIRECT QUOTES: 9** (2 airtrain-A, 4 airtrain-B, 1 hbomax-A, 1 hbomax-B, 1
warehouse-A, 0 in both selfcheckout pieces and warehouse-B). **2 of the 9 are attributed
to apparently-real, non-pseudonymized named public figures** (Kevin Irvine, Aimi
Hamraie) — the most serious single subclass found.

**UNSUPPORTED FIRST-PERSON EVENTS:** 11 distinct fabricated scenes/activities, plus 3
additional "canon-consistent general practice, new specific episode" cases (a softer,
but still real, violation class).

**HOW MUCH BLIND-REVIEW PRAISE DEPENDED ON UNSUPPORTED MATERIAL?** Of 14 specifically-
praised passages checked against provenance, 8 were APPARENT RICHNESS built on
fabricated material, 2 were MIXED, and 4 were EARNED. The single highest score in the
whole AR2 dataset (`selfcheckout-A`'s W=5) rests explicitly on fabricated biography for
the persona with the strictest real-person authorization standard in the system.

**AR2 QUALITY EVIDENCE: PARTLY INFLATED.** Not robust (too much of the specific praised
evidence is fabricated to call the absolute quality signal trustworthy as reported), and
not materially compromised in the sense of invalidating the whole experiment (the
underlying conceptual mechanisms independently survive removal of the fabricated
material in every single article, and the specific A-vs-B relative comparison was not
differentially confounded, since both arms shared the exact same uncontrolled testimony-
quota pressure).

**AR2 CAUSAL CONCLUSION: STANDS WITH QUALIFICATION.** The claim that writer doctrine
(AUTHOR RULE vs. Silent-Lens) is not the primary driver of subject-drift survives, and is
arguably reinforced by identifying the *actual* likely driver of the richness both
conditions displayed. The claim that AR2 demonstrated two doctrines both producing
strong, trustworthy finished work does not survive unqualified.

**DOES CURRENT PROMPT IMPOSE A TESTIMONY QUOTA? YES.** Direct, explicit, "NON-NEGOTIABLE"
language with no zero-testimony escape valve, contradicting the whitepaper's own stated
doctrine in as many words.

**"STRONG THESIS FROM SENTENCE ONE" CONFLICT: YES**, against the writer prompt's own
later "never state it" instruction and the whitepaper's discovery doctrine — currently
resolved in practice (behavior consistently favors withholding), but a real,
unreconciled inconsistency in the prompt text itself.

**DISCOVERY-MOTION EXPERIMENT READY: YES** — designed above, not run.

**UNEXPECTED-CORNERS DESIGN READY: YES** — six candidate archetypes designed above, none
selected or verified as final sources yet.

**UPSTREAM 2x2 DESIGN READY: YES** — designed above, explicitly sequenced *after* the
discovery-motion experiment, not before, given this audit's findings.

**ARTIFACT PATH:**
`.claude/experiments/artistic-reset-ar2-1-provenance-and-discovery-motion-2026-08-17.md`

**COMMIT / PUSH:** docs-only, to be committed and pushed to `origin/main` following this
document, per instruction.

**PRODUCTION CHANGES: NONE.**

**Decision: AR21B — AR2 SIGNAL PARTLY DEPENDS ON UNSUPPORTED HUMAN MATERIAL;
DISCOVERY-MOTION EXPERIMENT SHOULD CORRECT THE PROMPT PRESSURE BEFORE FURTHER ARTISTIC
CONCLUSIONS.**

Not AR21A: too much of AR2's specific evidence (especially its highest individual score)
is built on material the writer was never given, to call the signal fully surviving.
Not AR21C: the underlying conceptual mechanisms survive fabrication removal in every
article, and AR2's specific doctrine-comparison conclusion is not differentially
confounded — both arms suffered the same uncontrolled pressure equally, so the
comparison itself, as distinct from the absolute quality read, remains usable evidence.
