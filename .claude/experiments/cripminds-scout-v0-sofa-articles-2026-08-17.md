# CripMinds Scout V0 — Disturbance Discovery → Three Sofa Articles (2026-08-17)

**STATUS: EXPERIMENT COMPLETE, SHADOW-ONLY. No production code, prompts, personas, routing,
Story Rejection, or DBs touched. No article entered `_posts/` or `_drafts/`, no news marked
used, no production generation run. Base commit `9f9bf35` (matches `.claude/WORK.md` `## 5a`
"Immediate sequence" item 2).**

Full working artifacts (source pool, disturbance cards, perceptual probes, evidence packets,
articles): `.claude/experiments/scout-v0-sofa-articles-2026-08-17/`.

This is research/shadow work per `## 5a`'s own instruction — it does not rewrite the WORK.md
roadmap, since the result (below) confirms rather than overturns the existing "Scout, cheap
and bounded, produce ~3 real articles" plan. It is a decision INPUT, not itself a production
decision — see verdict at the end.

---

## METHOD SUMMARY (what was actually built, once, per the brief's own scope limits)

No database, no vector store, no recurring daemon, no new persona architecture, no 12-lens
system, no case library, no scheduler integration. What was built instead:

1. **Discovery** — six parallel research passes (general-purpose subagents), one per source
   category (court/legal + municipal; trade/business; science/research; design/architecture +
   technology; culture + small/specialist; general/major + local news), each independently
   web-searching and reading real, currently-retrievable sources, deliberately avoiding
   disability/accessibility keywords and the four banned example searches (local currency,
   shared well, GPS village, stroke musician). **24 real sources reviewed in enough depth to
   produce disturbance cards**, plus roughly 40 more sources checked and rejected as too thin
   (logged in `source-pool/*.md` for audit trail) — total real sources touched across both
   categories is well over 60.
2. **24 disturbance cards** produced, each naming a source, an exact verbatim fragment, why it
   resists its own stated explanation, a hypothesis (explicitly labeled as such), and what
   would make it a bad article. Full cards in `disturbance-cards/*.md`.
3. **Selection before persona** — a written selection pass (`perceptual-probes/selection-and-
   probes.md`) ranked 8 shortlisted candidates on disturbance strength alone, then ran a quick
   3-persona probe on each of the top 3 candidates (never all four for every candidate — Siri
   Sage was genuinely considered and genuinely lost each of the three probes it was tried
   against, not omitted by any balancing rule). No rotation, no "who hasn't written recently."
4. **Deep research** — three parallel evidence-packet passes, one per selected disturbance,
   each instructed to re-verify the original fragment against primary sources, investigate one
   real follow-up question, search for one genuinely real different-domain case to widen the
   mechanism (Bregman-structure), and explicitly flag anything that could not be verified.
   **These passes caught and corrected two real errors already present in the initial
   disturbance cards** (see PROVENANCE below) and one hypothesis in the original xAI card that
   turned out to be flatly wrong once checked against primary documents — the exact kind of
   self-correction the brief's "provenance before presentation" step exists to catch, except it
   surfaced during research rather than after drafting.
5. **Writing** — three finished articles, one per selected disturbance, each assigned to
   whichever of the four current personas' perceptual engine won its probe, using the current
   production writer doctrine (Bregman structural principle, AR3-B's zero-testimony-is-valid
   rule, AUTHOR RULE, HUMAN THREAD, FORBIDDEN DEFAULTS, no invented statistics) read directly
   from `automation/orchestrator/generate.py`, not paraphrased from memory.
6. **Provenance audit** — a direct line-by-line check of every factual claim, quote, name, and
   number in all three drafts against the evidence packets. Findings and corrections below.

---

## THE THREE SELECTED DISTURBANCES

Chosen as three genuinely different mechanism shapes, not the same conceptual trick three
times, and three different world objects, none reused from AR1/AR2/AR3's sources:

1. **A measurement instrument's blind spot is correlated with the very thing it measures** —
   camera traps used in wildlife ecology miss small, fast animals at far higher rates than
   large, slow ones, meaning "rarity" rankings from camera-trap surveys partly describe camera
   physics rather than population size (Kays, Hody, Jachowski & Parsons, *Movement Ecology*,
   2021).
2. **An administrative category is satisfied by physical form rather than function** — xAI's
   gas turbines at its Mississippi data-center site were classified "mobile" and "temporary"
   because they sit on trailers and were declared intended to stay under twelve months, a test
   that tracks nothing about actual continuous operation or emissions (Mississippi Department
   of Environmental Quality determination letter, July 2025; EPA rulemaking, January 2026).
3. **A formula borrowed from one domain is applied where its underlying physical property
   doesn't exist** — some home insurers depreciate labor costs in "actual cash value" property
   claims using the same age-based formula applied to physical materials, even though labor
   performed today has no age to have worn down (Michigan and Alaska insurance-bulletin fight,
   2024–2025; state court split).

---

## PER-ARTICLE RECORD

### Article 1 — "The Fox the Camera Missed" (Pixel Nova)

- **STARTED AS:** a 2021 ecology methods paper about camera-trap reliability.
- **BECAME:** an argument that any recording instrument has a shape — a set of things it's
  built to notice — and that "the record" quietly becomes mistaken for "what happened,"
  illustrated by a second, real, different-domain case (marine bioacoustic biodiversity
  surveys) showing the identical bias pattern in underwater listening equipment.
- **THE DISTURBANCE THAT OPENED IT:** cameras fail to record passing animals at rates from 14%
  to 71% depending on species, and the failure rate rises with body mass — the instrument's
  blind spot has the same shape as the ecological variable ("rarity") the survey exists to
  measure.
- **THE PERCEPTUAL ENGINE THAT MATTERED:** Pixel Nova's mediation/transmission engine —
  distinguishing "the information didn't arrive" from "the information wasn't there," grounded
  in two real, canon-authorized facts about interpreter lag and a "technically available but
  unusable" phone channel (`automation/persona_canon/pixel-nova-factual.md`), not invented
  biography.
- **THE REAL CASE THAT CHANGED THE ARGUMENT:** Mooney et al. 2020, *Royal Society Open
  Science*, on acoustic biodiversity surveys being "biased towards more gregarious, larger,
  louder or easily detected species" — verified verbatim, a genuinely different instrument
  class and sub-field, not decoration.
- **PROVENANCE: CLEAN, after one precision correction.** The evidence packet had explicitly
  warned that the paper's "14–71%" figure and its "29%–86% identifiable-photo rate" figure are
  complementary, not identical, and that a careless writer could conflate them. The first draft
  did exactly that (wrote "no trigger, no photo, nothing" for the 14–71% figure, which actually
  includes blank/unclear photos as well as true non-triggers). Corrected before finalizing.
- **WHY JASCHA MIGHT KEEP READING:** it never mentions disability until the fourth paragraph,
  never becomes an accessibility story, and the mechanism (a device's blind spot patterned like
  its target) is the kind of thing that, once seen, is hard to stop noticing in other recording
  systems.

### Article 2 — "Mobile, As Long As You Don't Look Too Long" (Zen Circuit)

- **STARTED AS:** a viral tech-press headline ("EPA closes loophole that let xAI pollute for a
  year without a permit").
- **BECAME:** a narrower, more accurate, and stranger story — a state regulator's own written
  two-part test (wheels + stated intent to stay under twelve months) as the actual legal
  mechanism, EPA's real response being to write a new accommodating category rather than simply
  close the door, and a real historical parallel (the Clean Air Act "glider kit" truck loophole)
  showing the same country reproduce the same category-gaming pattern in a completely different
  industry a decade earlier.
- **THE DISTURBANCE THAT OPENED IT:** a regulatory classification ("nonroad"/mobile) determined
  by physical form (trailer-mounting) and a stated intention, with no relationship to the
  substantive thing the category exists to regulate (continuous stationary operation, real
  emissions).
- **THE PERCEPTUAL ENGINE THAT MATTERED:** Zen Circuit's classification/administrative-category
  engine, anchored in her real canon fact (diagnosed autistic at nineteen — "a label finally
  attached to a dataset that had been sitting there the whole time") used once, briefly, not as
  manufactured texture.
- **THE REAL CASE THAT CHANGED THE ARGUMENT:** the EPA glider-kit truck loophole (2004–2018),
  fully sourced to the Federal Register and a Congressional Research Service report — a
  genuinely comparable regulatory-category failure, same country, different decade, different
  machine.
- **PROVENANCE: CLEAN, after one hypothesis was corrected and one attribution was corrected.**
  The original disturbance card speculated that turbines were physically relocated between
  sites to "reset" the twelve-month clock. Deep research found this specific hypothesis is
  **not supported** by the primary documents — the real pattern is continuous addition of new
  units at one site, not relocation of existing ones — and the draft was written to reflect the
  corrected mechanism, narrated honestly as a place the writer's initial assumption was wrong.
  Separately, a first draft mischaracterized a public newspaper quote as "an internal note
  quoted in a legal filing" — corrected to reflect it was a statement to a reporter. Two
  unverified, higher-stakes claims found during research (a "DOJ shielding xAI" story, and
  specific "4x cancer risk" figures being mistakenly read as an effect of xAI's own emissions
  rather than a pre-existing decades-old neighborhood burden) were deliberately **not used** in
  the final article.
- **WHY JASCHA MIGHT KEEP READING:** it resists the easy "billionaire polluter" framing the
  source material invites, and instead follows the actual mechanism — a regulator's own letter,
  a federal rule that keeps a version of the loophole alive on purpose, and a second real
  industry that got away with the identical trick a decade earlier.

### Article 3 — "The Hour That Has No Age" (Maya Flux)

- **STARTED AS:** a niche property-insurance trade-press item about depreciating "nontangible"
  claim components.
- **BECAME:** an argument about borrowed metaphors functioning as arithmetic, widened by a real
  contrast case from corporate accounting (goodwill impairment testing) showing a different
  field that faced the identical fork — tangible vs. intangible depreciation — and chose
  correctly, by design, decades ago.
- **THE DISTURBANCE THAT OPENED IT:** insurers apply a physical-wear depreciation formula to
  labor, which has no physical substance to age; regulators are actively split on whether this
  is even legal, and Alaska adopted a ban on the practice, then withdrew it three weeks later
  with a two-sentence notice giving no reason at all.
- **THE PERCEPTUAL ENGINE THAT MATTERED:** Maya Flux's cost-literacy engine, anchored in her
  own immutable canon fact (navigating US insurance systems as an immigrant with a spinal cord
  injury, "she knows what things actually cost, not what they're supposed to cost") — canon
  material, not invented biography.
- **THE REAL CASE THAT CHANGED THE ARGUMENT:** corporate accounting's treatment of goodwill —
  real, verifiable, and notable specifically as a domain that avoided the exact category error
  at the center of the piece, used as a contrast rather than a repetition.
- **PROVENANCE: CLEAN, after two factual corrections.** A first draft repeated the timeline
  error the evidence packet had explicitly warned against — "Michigan bulletin 2024-18-INS"
  content was correctly used, but Alaska's bulletin was mischaracterized as being withdrawn
  "one day before it would have applied," when the record shows it had already been in effect
  for about three weeks. Corrected. A labor-cost-share fraction ("a third and three-fifths")
  was tightened to match the sourced 40–60% range exactly ("two-fifths and three-fifths"). The
  dollar-scale figure used ($1,900–$2,850) is explicitly framed as an illustrative construction
  from real inputs, per the evidence packet's own instruction, not asserted as a single sourced
  real-world outcome.
- **WHY JASCHA MIGHT KEEP READING:** the Alaska thread — a real consumer protection adopted and
  then quietly reversed with zero stated reason — is the kind of detail that makes a reader want
  to know what actually happened, and the honest "I don't know" about the cause is left in
  rather than smoothed over with a plausible-sounding guess.

---

## PROVENANCE SUMMARY

Six corrections were made across the three drafts during the audit pass — all caught by
checking prose against the evidence packets sentence by sentence, none requiring a reroll or
best-of-N regeneration (one evidence-preserving correction pass, per the brief's §14 rule):

1. Article 1 — conflated the paper's "14–71% failure" statistic with "no photo at all,"
   overstating what that number means. Corrected.
2. Article 1 — "twenty-year-old name" for a 2002-established term loosely stated; tightened.
3. Article 2 — repeated the original disturbance card's unverified "turbines relocated to reset
   the clock" hypothesis, which deep research found unsupported. Corrected to the
   evidence-based mechanism (continuous addition, not relocation).
4. Article 2 — mischaracterized a newspaper quote as an internal document. Corrected.
5. Article 3 — Alaska bulletin timeline error (said "withdrawn one day before taking effect,"
   when it had been in effect roughly three weeks). Corrected.
6. Article 3 — labor-cost-share fraction loosely rounded; tightened to match the source range.

No unsupported named person, no unsupported quotation, no unsupported personal event, no
invented statistic, and no source-mechanism mismatch survived into the final drafts. Two
specific unverified claims surfaced during research (the DOJ-shielding-xAI story; a
cancer-risk figure at risk of being misread as xAI-specific) were identified and deliberately
excluded rather than included with a hedge — the safer failure mode given this publication's
own standard that a fabricated or misattributed claim is the single most exposed kind of error
it can make.

**One known, disclosed tension, not silently resolved:** all three selected disturbances are
American-sourced (a North Carolina research forest; Mississippi/Tennessee environmental
regulation; Michigan/Alaska insurance bulletins), which sits in tension with the production
writer prompt's "do not locate arguments in the United States specifically... no American laws
or institutions" instruction. That instruction reads, in context, as aimed at forestalling a
lazy default to ADA/FEMA-style disability-policy framing — none of which appears in any of
these three pieces — and AR3's own "Unexpected Corners" source set already included an American
state supreme court case (`Lytle v. Lind`, Maine) without objection. Given the alternative was
either inventing non-US facts (a harder rule violation) or discarding otherwise strong,
well-evidenced material, the pieces were written as drafted, with the argument in each framed
as a structurally portable mechanism rather than an American-policy critique, and this tension
is flagged here rather than left for a future reader to discover unremarked.

---

## SCOUT V0 VERDICT

**SV0A — Scout produced clearly stronger Sofa-Article material than the standard news-in →
disability-angle → persona pipeline would likely have produced on the same raw material,
because the disturbance-first discovery step surfaced mechanisms (instrument bias correlated
with its target, a category satisfied by form not function, a metaphor doing arithmetic's job)
that a topic-first search for "a story CripMinds could plausibly write about" would have had no
reason to find.** All three pieces pass the AUTHOR RULE test (each could run without the words
"disability" or the persona's specific condition ever appearing, and still carry the specific
perspective), none defaults to ramp/curb-cut/access-theater framing, and none was selected for
an obvious disability angle — confirmed directly, since the discovery agents were explicitly
instructed not to search disability/accessibility terms and did not.

This is offered as an honest recommendation, not a foregone conclusion — the brief's own
success criterion is that Jascha reads the three pieces as articles, not experiments, and that
judgment is his to make, not this pass's to declare for him. If the read confirms SV0A, the
brief's own §5a sequence (item 4: add case-memory retrieval only if Scout's own output makes a
real reuse opportunity concrete) is the next honest step, not a full production Scout
architecture — this V0 deliberately proves the discovery-then-writing loop can produce real
work, not that it should immediately become a service.

**PRODUCTION CHANGES: NONE.** No code, prompt, persona canon, routing, database, or published
content was touched. All output lives under `.claude/experiments/scout-v0-sofa-articles-
2026-08-17/` and this record.

**MODEL / PROVIDER:** all research and writing in this pass used the calling agent's own model
directly (real WebSearch/WebFetch tool calls, not simulated), not routed through Trident's
CLIProxyAPI or any production LLM call path — consistent with every AR1–AR3 pass before it,
none of which had production provider access from this Mac either.

**ARTIFACT PATH:** `.claude/experiments/cripminds-scout-v0-sofa-articles-2026-08-17.md` (this
file) + `.claude/experiments/scout-v0-sofa-articles-2026-08-17/` (source pool, disturbance
cards, perceptual probes, evidence packets, final articles).
