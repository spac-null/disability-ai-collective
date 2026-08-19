# Writer Grounding — Test 2

Shadow-calibrated modular architecture, run on the frozen draft (`run/article.md`).
**Adjudicated directly against the frozen RAIB source**
(`source/source-snapshot.txt`, SHA-256 `be381bbc…`).
**Gold V2.1 was not used as a detector input.** It is Edinburgh-only calibration evidence
and is not Test-2 truth.

Doctrine applied: CripMinds may create new meaning from grounded facts. It may not create
new factual states about the world, people, the driver, the pedestrians, or the report
without evidence. Interpretation is not patched merely because RAIB does not state it
verbatim.

---

## Stage 1 — Faithful extraction

61 factual commitments extracted from the article, by class:

| Class | Count |
|---|---|
| Physical layout of the crossing | 11 |
| The warning system: devices, rules, training, board | 12 |
| Standards and recorder behaviour | 4 |
| The shift and the tram | 5 |
| The two pedestrians and their run | 8 |
| The accident sequence | 10 |
| Recorder findings | 3 |
| Prior occurrences | 6 |
| Remedy line | 2 |

## Stage 2 — Commitment decomposition

Each commitment decomposed into (a) the factual state asserted, (b) whether the source
asserts it, (c) whether any qualifier attaches, (d) whether the article preserves it.

**Qualifier preservation — the watchlist's central test:**

| Source qualifier | Source text | Article text | Preserved |
|---|---|---|---|
| "probably" | "it is therefore probably the case that the tram driver did not sound an audible warning as required" | quoted verbatim | ✔ |
| "possibly" | cobbles "possibly exacerbated one of the pedestrian's injuries" | "which possibly exacerbated one pedestrian's injuries" | ✔ |
| "could have addressed" | "could have addressed the inconsistencies in audible warnings" | quoted verbatim | ✔ |
| "may have been" (2008 headphones) | "may have been wearing headphones" | "may have been wearing headphones, which would have prevented them hearing" | ✔ |
| "may have been negatively affected" (2005 fence) | same | "may have been negatively affected by the fence" | ✔ |
| "seemingly unaware" (2016) | same | "seemingly unaware it was approaching" | ✔ |
| "unclear" (cab footage) | "the footage is unclear as to whether they did so or not" | "the footage cannot resolve whether they did" | ✔ |
| "appropriate" / "adequate length" | quoted | quoted, and the repetition across documents is shown not asserted | ✔ |
| "approximately" (distances/speeds) | throughout | "approximately", "around", "about", "roughly" retained throughout | ✔ |

No qualifier was silently hardened into certainty.

**Watchlist items, adjudicated:**

| Watchlist item | Finding |
|---|---|
| exact seconds / times / distances / speeds | All 14 figures match the source exactly (09:46, 15:46, 16:14, ~17 mph, 30 mph, 15 mph, ~13 mph, ~30 m board, ~30 m hazard brake, 45 m / 40 m / 5 m / 24 m fence, ~6 m carried, ~4 s, ~12 m, ~30 passengers, 1.2 km, ~6 min). No figure invented. |
| who rang bell or horn | The article never states the driver rang the bell. It reports the driver's statement, the footage's inability to resolve it, the absent recorder log, and RAIB's "probably". Correct. |
| what the recorder can and cannot distinguish | Article states the recorder logs "bell and horn activation on the same channel" (quoted) and separately that no bell was logged at the board. It does **not** claim the recorder cannot tell them apart — a claim the source does not make. Correctly restrained. |
| driver's motives / decisions | No motive, no reason, no fault, no cab scene, no interior life. The driver's hand on the control is reported as the source reports it. |
| pedestrians' knowledge / expectations | Only what the source states: unfamiliar with the area and tram networks, had never encountered a tram while crossing, did not look. The source's "witness evidence shows neither pedestrian was expecting to have to stop for a tram" is not used, and nothing stronger is asserted in its place. |
| "fewer than ten" crossings | **Article is more accurate than the frozen prompt.** The prompt's landing says they "had crossed this tramway fewer than ten times"; the source says they had completed the *circuit* fewer than ten times, and the circuit crosses the tramway twice. The article writes "on every previous circuit those two runners had made — fewer than ten of them". Correct against source. |
| claims about every prior silence | See **F2** below. |
| recurrence across previous incidents | Five prior occurrences reported exactly as the source records them; no aggregation, no casualty total, no "pattern of deaths" characterisation. |
| claim that remedies were all directed at the sender | **Not asserted.** The article writes "The remedies form their own line" and then lists them, including the 2005 fence redesign — which was not directed at the sender. It shows the line without overclaiming its uniformity. Correct. |
| causation vs "could have addressed" | Preserved verbatim. The article nowhere says the accident was preventable or that any remedy would have prevented it. |
| visual / hearing redundancy | The article reads the source's "or" as presenting the two "as though either would do". This is a reading of a quoted sentence, not an attribution of a redundancy claim to RAIB. Legitimate interpretation. |
| any acoustic performance claim | None. No decibels, frequencies, or audibility distances. The only loudness statements are the source's own — devices "sounded clearly", and the 2018 quote "not sufficiently loud". No claim about how loud or quiet a tram is. |

## Stage 3 — Negative source proof

For each suspected unsupported commitment, the source was searched for supporting text.

- **Elapsed-interval claim.** `grep -i "nine years|ten years|years later|years after"` over the
  full source returns **no match**. The source states no elapsed interval anywhere.
- **Track-clear claim.** The only supporting sentence is line 846: "and had never encountered
  a tram while crossing the tramway." Nothing states the track was clear on those occasions,
  or that the pedestrians observed silence.
- **Recommendation addressee.** Line 1356: recommendation 1 was addressed to "Stagecoach
  Supertram". The article says "the operator".

## Stage 4 — Deterministic modular arbitration

| ID | Commitment | Class | Verdict |
|---|---|---|---|
| **F1** | "Nine years later, RAIB records that…" | writer-computed temporal figure | **TRUE UNSUPPORTED** |
| **F2** | "…fewer than ten of them, none with a tram on the track…" | strengthening of a narrower source claim | **TRUE UNSUPPORTED** |
| F3 | "RAIB recommended that the operator review its operational standards" (2017 recommendation was addressed to Stagecoach Supertram) | entity continuity | **TRUE UNCERTAIN** — no patch |
| F4 | "Its ordinary state is silence." | interpretive characterisation of a sent-message channel | **LEGITIMATE INTERPRETATION** — no patch |
| F5 | "looking is a property of the crossing. The sightline is there whenever anyone is" | conceptual claim about looking, not a measured claim about this crossing's sightlines | **LEGITIMATE INTERPRETATION** — no patch |
| F6 | "the silence had been true" | inference from "never encountered a tram while crossing" | **LEGITIMATE INTERPRETATION** — no patch (the underlying factual state is source-given; the reading is the article's) |
| F7 | "A channel that is almost always silent… teaches the people who use it that silence is information." | the article's discovery | **LEGITIMATE INTERPRETATION** — no patch |

### F1 — detail

> "Nine years later, RAIB records that more effective implementation of that recommendation
> 'could have addressed'…"

The sentence's own anchor is "After the death at Woodbourn Road in 2016". RAIB records this
in Report 10/2026, published July 2026 — **ten** years after that death. Nine years is only
correct if measured from report 13/2017 to report 10/2026, which is not the anchor the
sentence sets. The source supplies no interval at all. This is a writer-introduced computed
figure that is both unsupported and, against its own anchor, wrong.

### F2 — detail

> "…on every previous circuit those two runners had made — fewer than ten of them, none with
> a tram on the track — the silence had been true."

The source supports: they completed the circuit fewer than ten times, and never encountered
a tram while crossing the tramway. "None with a tram on the track" asserts something wider —
that no tram was on the track during those circuits — which the source does not establish. A
tram could have been on the line without being encountered at a crossing.

## Stage 5 — Findings

**TRUE UNSUPPORTED: 2** (F1, F2)
**TRUE UNCERTAIN: 1** (F3, no patch — patching would require naming entities the article
deliberately does not name, damaging prose to fix an ambiguity RAIB itself carries)
**LEGITIMATE INTERPRETATION, CORRECTLY NOT FLAGGED: 4** (F4–F7)

**Failure classes represented:**
1. **Writer-computed figure** — a number derived by arithmetic rather than taken from the
   source (F1). Not a hallucination of fact; a hallucination of *interval*.
2. **Quantifier widening** — a narrow source claim restated over a wider domain (F2).

Neither is a fabrication of an entity, quote, name, measurement, or event. No invented
person, no invented quotation, no invented measurement, no motive, no scene. The two
failures are both at the boundary where the article compresses source facts into its own
summary clause.
