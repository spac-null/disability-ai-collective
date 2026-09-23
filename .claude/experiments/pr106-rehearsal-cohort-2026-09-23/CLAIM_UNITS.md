# Labelled claim units — seed set for the definitions-only claim-support shadow

Human labels, assigned by reading the full propositions and support spans. Four statuses:
`SUPPORTED`, `NOT_ESTABLISHED`, `CONTRADICTED`, `NON_FACTUAL_OR_NOT_CHECKABLE`.

`NOT_ESTABLISHED` is not `CONTRADICTED`. The question is never whether a claim is true in
the world; it is **may this article say this, given its frozen evidence.**

Every unit below is scored against **only that definition's declared `definition_evidence`**,
never the whole ledger. Widening the evidence set is what lets an unrelated fact rescue an
unsupported commitment, which is the failure the 114-run relation audit demonstrated.

The positive controls matter as much as the target. A detector that flags `minutes away` by
distrusting the whole gloss is worthless; the test is whether it flags that commitment while
leaving the seven supported ones alone.

---

## Unit 1 — run 1 · `Dressing for Evacuation` · THE TARGET CASE

Gloss:

> A research project in which people were asked to put on what they would wear if told a
> large-scale evacuation were minutes away, and to gather a limited selection of belongings;
> what a person chose was recorded in a photoshoot and an accompanying survey, and shown as
> life-size portraits.

Declared evidence — `[F46, F47, F48]`, full propositions:

- **F46** — "In the project Dressing for Evacuation, participants were asked to dress as if
  alerted to an imminent large-scale evacuation, and responses were recorded in a photoshoot
  and accompanying survey."
- **F47** — "Dressing for Evacuation culminated in life size photographic portraits shown at
  the Tentworks exhibition at the Feverish World Symposium in 2018 in Vermont, USA, and at
  the Fashion and Textiles FutureScan 4 Conference at the University of Bolton, UK, in 2019."
- **F48** — "Dressing for Evacuation focuses on the human emergency response of getting
  dressed and gathering a limited selection of possessions."

| # | atomic commitment | label | evidence |
|---|---|---|---|
| 1.1 | People were asked to put on what they would wear | `SUPPORTED` | F46 |
| 1.2 | The scenario was a large-scale evacuation | `SUPPORTED` | F46 |
| 1.3 | The evacuation was presented as imminent | `SUPPORTED` | F46 |
| 1.4 | **The evacuation was specifically minutes away** | **`NOT_ESTABLISHED`** | **none** |
| 1.5 | Participants gathered a limited selection of belongings | `SUPPORTED` | F48 |
| 1.6 | Choices were recorded in a photoshoot and an accompanying survey | `SUPPORTED` | F46 |
| 1.7 | Results were shown as life-size portraits | `SUPPORTED` | F47 |
| 1.8 | It is a *research* project | `NOT_ESTABLISHED` | none in the declared set — F46/47/48 say "project", not "research project". Marked separately from 1.4 because it is a weaker, arguably non-material case and a detector may reasonably differ. |

No fact in the entire run-1 ledger contains "minutes". `minutes` appears at exactly one line
of `WRITER_PACKET.txt` — line 64, the `EXPLAIN AT FIRST USE` block.

Downstream consequence: 3 of 6 blocking Grounding findings carry the phrase.

Success criterion for the shadow: flag **1.4**; do not flag 1.1–1.3, 1.5–1.7.

---

## Unit 2 — run 1 · `fictional participatory scenario` · POSITIVE CONTROL

Gloss:

> Research that invents an emergency, asks people to act as though it were happening, and
> documents their responses as a work.

Declared evidence — `[F43, F45, F46]`:

- **F43** — "Curtis's academic research creates fictional participatory scenarios responding
  to climate impacted emergencies."
- **F45** — "Curtis's research project Imagining Neutopia fabricates and documents fictional
  events to further climate change discourse."
- **F46** — as above.

| # | atomic commitment | label | evidence |
|---|---|---|---|
| 2.1 | The research invents an emergency | `SUPPORTED` | F43, F45 |
| 2.2 | People are asked to act as though it were happening | `SUPPORTED` | F43, F46 |
| 2.3 | Responses are documented as a work | `SUPPORTED` | F45 |

Expected: **zero warnings.**

---

## Unit 3 — run 3 · `commercial whaling quota` · POSITIVE CONTROL

Gloss:

> the number of animals that licensed vessels are permitted to take in a given year under
> national regulation; Norway is one of the few countries that still allows this for
> commercial purposes

Declared evidence — `[F69, F70, F71]`:

- **F69** — "Norway is one of the few countries that continues to permit commercial whaling,
  specifically the hunting of minke whales."
- **F70** — "Under the 2026 regulations, licensed Norwegian vessels were allocated a total
  quota of 1,641 minke whales."
- **F71** — "The Norwegian government argues the hunt is based on sustainable management of
  an abundant population, while commercial whaling remains internationally contested."

| # | atomic commitment | label | evidence |
|---|---|---|---|
| 3.1 | A quota is a number of animals licensed vessels may take | `SUPPORTED` | F70 |
| 3.2 | It is set for a given year under national regulation | `SUPPORTED` | F70 |
| 3.3 | Norway is one of few countries still permitting commercial whaling | `SUPPORTED` | F69 |

Expected: **zero warnings.** Note 3.1–3.2 are partly general-knowledge framing of a term; a
detector may reasonably return `NON_FACTUAL_OR_NOT_CHECKABLE` for them. That is acceptable.
Returning `NOT_ESTABLISHED` is not.

---

## Unit 4 — run 3 · `knowledge and experience centre` · POSITIVE CONTROL

Gloss:

> the category the developers use for what they are building: a place set up to explore
> whales, the ocean, and how the relationship between people and cetaceans is changing

Declared evidence — `[F73]`:

- **F73** — "The Whale will not operate simply as a traditional natural history museum; its
  developers describe it as a knowledge and experience centre exploring whales, the ocean and
  the changing relationship between people and cetaceans."

Near-verbatim. Expected: **zero warnings.** This is the cleanest available negative control.

---

## Unit 5 — historical diagnostic · `block group` · HISTORICAL CONTRACT

From the held-out real architecture (`.claude/story-architecture/held-out-real-article-1/`),
which **predates `definition_evidence`** and declares none. Evidence assigned by hand for
diagnostic purposes only — mark any result as historical, not current-contract.

Gloss:

> the smallest area the survey publishes figures for

Nearest available evidence:

- **F19** — "Where a block group's sample is too small or unreliable, the ACS publishes no
  estimate, and both the device and the map render this as no reading rather than as zero."

| # | atomic commitment | label | evidence |
|---|---|---|---|
| 5.1 | A block group is an area the survey publishes figures for | `SUPPORTED` | F19 |
| 5.2 | **It is the *smallest* such area** | **`NOT_ESTABLISHED`** | **none** — no fact in the frozen manifest asserts the superlative |

This is the minimal pair in its purest form: the same sentence is supported without
"smallest" and unsupported with it.

---

## Not in this set

Run 3's `entrance gallery` belongs to `PACKAGE_AUTHORED_UNSUPPORTED_SPECIFICITY` and is out
of scope for a definitions shadow. It is recorded in `README.md`.

An earlier draft of this file listed run 3's `communication, cooperation, caregiving` as a
second target case. That was an error — F18's full span licenses the triad explicitly, and
the misreading came from a truncated 160-character display. See the correction section of
`README.md`. **Score claim units against full propositions and support spans only.**

## Size and honesty about it

13 labelled units across 5 definitions, 3 of them from 2 natural current-contract
architectures. Two are true `NOT_ESTABLISHED` targets; one of those is historical. This is
enough to expose a detector that flags everything or nothing. It is **not** enough to
establish precision. More natural runs are required before any promotion discussion.
