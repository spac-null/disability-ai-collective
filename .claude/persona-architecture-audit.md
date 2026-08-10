# Persona Architecture Audit (Phase 1.5A)

Design/audit only. No `personas.py`/`generate.py` edits, no generations, in
this document. Extracted from `automation/persona_canon/*.md` (biography),
`automation/orchestrator/personas.py` (`AGENTS[...]["prompt_block"]`, the
generation-time voice brief), and `automation/orchestrator/generate.py`
(topic-routing logic + global rules). Six categories per persona: CORE
PERSON, PERCEPTUAL ENGINE, MOTIVE, AFFINITY, RISK, TEXTURE — see
`.claude/current-work.md`'s `PERSONA ARCHITECTURE / TERRITORY AUDIT`
section for why "affinity" replaces "territory."

## Cross-persona findings first (these matter more than any single row)

**1. Confirmed hard-territory mechanism #1 — Siri Sage's VOICE ANCHOR
(`personas.py` line 26), verbatim:**
> "Your territory is phenomenological, not structural... Not spatial
> legibility. Not wayfinding systems. Not information architecture. Those
> belong to Pixel Nova."

This is a textual OWNERSHIP CLAIM, not an affinity. It doesn't just steer
Siri toward her strength (acoustic phenomenology, which is real and good) —
it explicitly forbids her from a category by name and assigns that category
to a named colleague. Already flagged in the editorial blueprint (memory
`project_cripminds_editorial_blueprint.md`) as a found bug; this audit
confirms it's the ONLY explicit "belongs to X" sentence in any of the four
`prompt_block`s — Pixel/Maya/Zen's blocks contain no equivalent claim about
Siri or each other.

**2. Confirmed hard-territory mechanism #2 — global FORBIDDEN DEFAULTS
(`generate.py` line 591), verbatim:**
> "Do not build your argument around ramp, curb cut, grab rail, tactile
> paving, accessible toilet, or lift as the central concrete example."

This rule is NOT persona-specific — it applies to whichever persona is
writing. But it collides almost entirely with ONE persona's canon: Maya
Flux's `FIXED BELIEFS` open with "the ramp on the blueprint" as "the only
measurement that matters," her `WOUND` is a three-step wedding venue, her
`THE INDEFENSIBLE` is about broken sidewalks. A rule written to stop every
persona from defaulting to the easiest disability image mostly disables
Maya's actual evidentiary vocabulary. This is the second, independently-
discovered instance of the same failure mode the blueprint found for Siri:
an anti-cliché rule banning a persona's most epistemically load-bearing
material, not just a generic crutch.

**3. Hard-territory mechanism #3, at the routing layer, not just the prompt
— `generate.py` lines 161-168:**
```python
if any(word in domain_lower for word in ['art', 'design', 'visual']):
    _preferred = "Pixel Nova"
elif any(word in domain_lower for word in ['tech', 'science', 'system']):
    _preferred = "Zen Circuit"
elif any(word in domain_lower for word in ['culture', 'social', 'entertainment']):
    _preferred = "Siri Sage"
else:
    _preferred = "Maya Flux"
```
Persona selection for discovery-sourced articles is a hard keyword→persona
map — topic assignment, exactly what the "affinity not territory" principle
is meant to replace. Maya is the ELSE/default bucket: she gets everything
that doesn't match an art/tech/culture keyword, which should mean high
volume, not low. But `generate.py`'s own comment (line 242-243) records
60-day published-article totals: **Zen Circuit 14, Pixel Nova 9, Siri Sage
7, Maya Flux 4** — Maya is lowest despite being the routing default. The
likely mechanism: she's frequently selected by this router, then loses
articles downstream — either FORBIDDEN DEFAULTS weakening her drafts (item
2 above), or Fable's own brief-writing (`_fable_editorial_brief`) preferring
a different persona for the same source and `_balance_agent` honoring that
override (line 236-253). Not fully diagnosed from static text alone — worth
a targeted look at rejected/degraded Maya drafts if this audit's findings
get acted on, but the routing-layer keyword map is a real hard-territory
mechanism regardless of which downstream cause dominates.

**4. No prompt-mandated tic/wound injection found.** None of the four
`prompt_block`s contain machinery forcing a specific anecdote into every
essay — the wound/indefensible-opinion material is framed as background
("here is what you don't put in your talks"), not a checklist item. The
repeated-anecdote pattern the blind-comparison agents noticed in practice
(e.g. Maya's "wedding, three steps" recurring near-verbatim across samples)
is a generation-tendency/repetition problem, not a prompt-architecture
defect — it's already Phase 5's territory (the repetition judge), not this
audit's.

**5. No persona has an explicit MOTIVE statement.** None of the four
`prompt_block`s contain a "what I want to give the reader" / "why I write"
sentence — this matches the blueprint's still-pending Phase 3 item
("WHAT I BRING BACK" per persona). Confirmed missing for all four, not
persona-specific — a genuine gap to fill in Phase 3, not evidence any one
persona is broken.

**6. Relational overlaps are already self-aware, not redundant.** Every
pairing in each canon file's `RELATIONSHIP TO OTHER PERSONAS` section states
a specific, distinct axis of disagreement (Siri/Pixel: phenomenological vs.
structural primacy; Siri/Zen: record vs. optimize; Maya/Zen: rebuild vs.
see-correctly; Maya/Pixel: infrastructure vs. representation, "ramps come
first" but "not a distraction"; Maya/Siri: infrastructure vs. phenomenology
as the more urgent register; Zen/Pixel: temporal/network vs. visual
organization of the same object, e.g. the tube map). This is well-designed
on paper. Whether it holds in actual generated prose — whether two personas
converge on the same mechanism when facing the same real source — is
exactly what the future same-source/four-persona probe is for, and cannot
be answered from static text. Not a finding, a correctly-deferred question.

## Per-persona matrix

### Siri Sage
- **CORE PERSON**: Blind since six (retinal detachment, both eyes a year
  apart); Edinburgh working-port upbringing, scholarship-kid navigation of
  institutions; acoustic-design formation (Edinburgh, RCS composition,
  STEIM/Djerassi/Atelier Calder residencies, 3 years field-recording cities
  before/after renovation).
- **PERCEPTUAL ENGINE** (clearest of the four, explicitly restated in the
  VOICE ANCHOR): space is acoustic before it is visual; a room's silence is
  a political choice about whose discomfort is acceptable; what does a
  space do to a body that arrives through sound, and what does silence
  force that body to do. This is a real, portable question — testable on
  any object, not bound to "blindness" topics.
- **MOTIVE**: absent as a stated sentence. Closest available material: her
  canon's closing line under `THE WOUND` — "she has spent fifteen years
  building arguments about what she *can* give that nobody else can" —
  gestures at a motive (give back what only this perceptual mode notices)
  but it's backstory commentary, not a brief-facing instruction.
- **AFFINITY** (not ownership): acoustic/sensory-rich environments, radio,
  sound art, blind visual-art history — these are where her engine is
  CHEAPEST to apply well, not where it's exclusively valid.
- **RISK**: the VOICE ANCHOR's explicit prohibition (finding #1) is itself
  the risk — it forecloses exactly the territory (spatial legibility,
  wayfinding) where her acoustic engine might produce the sharpest, least
  expected essays (a wayfinding system evaluated by ear, not eye, is a
  genuine category jump, not a Pixel-Nova encroachment). Secondary risk:
  the wound (roommate, "I need someone who can see my face") is
  emotionally resonant but doesn't generate the perceptual engine the way
  the other three personas' wounds do (see Zen/Maya/Pixel below) — it's
  CORE PERSON material, not PERCEPTUAL ENGINE material, and shouldn't be
  forced into that role.
- **TEXTURE**: wind chimes (nine sets, "acoustically incoherent," loves
  them anyway), 5:45am pool-doorway listening ("greed," not research),
  weather-by-puddle-probability shoe choice. Genuinely optional, not
  weaponized in the prompt.

### Zen Circuit — scrutinized hardest per the WHY WE WRITE data (the one
persona whose "why this writer"/"what did they give me" scores dipped
under the new doctrine, even as doctrine-leak improved the most of any
persona — suggesting the shared doctrine isn't Zen's problem; something in
her EXISTING architecture may already be capping how irreducible her
essays can get)
- **CORE PERSON**: autistic, diagnosed at 19 ("a label for a dataset that
  was always there"); Stockholm/Vällingby upbringing in a transit-oriented
  planned suburb, engineer father at Swedish Railways; KTH transport-
  systems formation, Crossrail consultancy, London since 2012.
- **PERCEPTUAL ENGINE**: scattered across "obsessions" (list-shaped: how
  diagnostic categories get invented, special interests as dismissed
  expertise, sensory experience as data) and "fixed beliefs" (argued
  positions: "pattern recognition is expertise... an epistemological
  failure of the observer," "the neurotypical norm is a statistical
  artifact promoted to a moral standard") rather than condensed into one
  perceptual question the way Siri's is. The sharpest candidate, synthesized
  from her `FROM THE INTERVIEWS` material (the till/change story, the
  albino-diagnosis story) rather than stated outright anywhere: **she
  notices when a system's classification of a person's competence (a
  diagnosis, a test score, a read of someone's affect) is actually a
  statement about the limits of the system's OWN measurement, misattributed
  to the person being measured.** That is a real, portable engine — testable
  on a supermarket self-checkout's "customer error" logging, a school
  timetable's "disruptive student" flag, a dating app's compatibility
  score — not bound to employment/algorithm topics. It is currently
  IMPLICIT, not written into the brief.
- **MOTIVE**: absent as a stated sentence, same gap as all four. Closest
  material: "special interests are not symptoms... the output is usually
  better than the credentialed alternatives" — argues FOR her way of
  attending, doesn't yet say what she wants the reader to leave with.
- **AFFINITY**: transit/systems/diagnosis topics are where her formation
  makes the engine cheapest to apply — not where it's exclusively valid.
- **RISK — the one worth the closest look**: her `WRITING VOICE` section
  (unique to Zen; none of the other three personas have an equivalent
  block in `personas.py`) is entirely STRUCTURAL (open with scene never
  definition, jargon only once earned, short punches at section ends,
  sparing first-person) — it specifies HOW she writes in detail but not
  WHAT she's for. Combined with the perceptual engine being implicit
  rather than stated, Zen may be the most mechanically well-specified and
  least epistemically anchored of the four — which fits the WHY WE WRITE
  data: a shared publication-level motive (WHY WE WRITE) has less to
  attach to when the persona's OWN motive/engine isn't load-bearing in the
  brief. This is a real candidate explanation for her dip, and the fix
  (surface the implicit engine above, add a motive sentence) belongs in
  Phase 3, not in revisiting WHY WE WRITE.
- **TEXTURE**: starling murmurations ("not a system... the math is
  secondary to the thing itself" — notably, texture that CONTRADICTS her
  own engine, which is a good sign of a real character rather than a
  thesis-delivery-device), Tuesday oatmeal/transit-feeds/desk-drawer
  ritual.

### Maya Flux
- **CORE PERSON**: T6 incomplete spinal cord injury at 15 (São Paulo,
  Marginal Pinheiros highway); working-class Santo André upbringing, bus-
  driver father; Pratt urban planning, CUNY disability-studies fellowship,
  Brooklyn since 2008, undocumented-immigrant navigation of US insurance
  systems with a spinal injury.
- **PERCEPTUAL ENGINE**: also list-shaped on the surface ("obsess over the
  gap between disability policy and physical reality... the ramp, the curb
  cut, the lift") but her `FIXED BELIEFS` contain the real, sharp version:
  **the gap between what a design promises on paper and what it does on a
  specific Wednesday is the only measurement her field refuses to make** —
  a genuine, portable attention (applies to a supermarket self-checkout's
  advertised accessibility vs. its actual queue behavior, not just ramps).
  Directly collides with FORBIDDEN DEFAULTS (finding #2) when the concrete
  anchor happens to be a ramp/curb-cut/lift, which for a mobility-disability
  persona is often the MOST honest available anchor, not the laziest one.
- **MOTIVE**: absent as a stated sentence, same gap as all four. Closest
  material: "care work is labor... the economy is lying about how it
  works" and her wound's closing line about efficiency at "making it easy
  for the people who failed to plan" — gestures at exposing the labor of
  compliance-without-dignity, not yet a brief-facing sentence.
- **AFFINITY**: mobility/urban-infrastructure/protest-history topics —
  cheapest application, not exclusive claim.
- **RISK**: FORBIDDEN DEFAULTS (finding #2) is the dominant risk — it's a
  global rule that happens to disable one persona's central evidentiary
  vocabulary far more than the other three's. Combined with the routing
  layer making her the ELSE-bucket default (finding #3) while her
  published count is lowest of the four, this is the strongest concrete
  candidate for "an anti-cliché rule accidentally prohibiting a persona's
  most epistemically valuable territory" the blueprint predicted for a
  second persona beyond Siri.
- **TEXTURE**: Prospect Park West hill speed ("the best feeling she
  knows"), broken-sidewalk tree-roots aesthetic ("she cannot defend this"),
  Tuesday plantains/tire-pressure/MTA-horoscope ritual.

### Pixel Nova
- **CORE PERSON**: Deaf since birth (no before/after); Amsterdam→Bijlmer
  upbringing, typesetter father who lost his trade to machines; Rietveld/
  KABK typography formation, Brooklyn since 2011.
- **PERCEPTUAL ENGINE**: partially explicit — "information architecture
  that reveals or conceals power," legibility as a political act — but
  delivered as a long list of interests (sign-language linguistics, Flusser
  on images-vs-text, isotype's failure, wayfinding) rather than one
  question. The sharpest single-sentence version, present but buried in
  her canon's `FIXED BELIEFS`: **legibility is a political act; so is
  illegibility; the choice of which to value is never neutral** — a real,
  portable attention (applies to any system that decides what gets shown,
  delayed, or hidden — museum labels, yes, but equally a supermarket
  pricing display or a hotel booking flow). Note the explicit correction
  already made this session (`.claude/current-work.md`): the museum-labels
  validation topic tests THIS engine under her current configuration; it
  does not make information architecture her territory.
- **MOTIVE**: absent as a stated sentence, same gap as all four. Closest
  material: the museum/Rothko wound's own framing — "as if seeing needed
  to be translated into knowing" — gestures at giving the reader unmediated
  access to what she sees rather than an explanation of it, not yet a
  brief-facing sentence.
- **AFFINITY**: visual/information/design/museum topics — cheapest
  application, not exclusive claim. (This is the affinity the current Pixel
  supplemental validation deliberately used — correctly, per the
  interpretation boundary already on record.)
- **RISK**: no explicit hard-ownership prohibition found in her own
  `prompt_block` (unlike Siri) — her risk is closer to Zen's: a rich
  interest-list without a single condensed engine-sentence, making it
  easier for a generation to drift into "AI-signage-raises-accessibility-
  questions"-shaped genericism if the source doesn't resist that pull (this
  is exactly why the museum-labels fixture was deliberately chosen for its
  ZERO pre-existing disability framing — a harder test than a softball
  would have been).
- **TEXTURE**: cheap bodega neon ("will cross four blocks for good neon...
  not rational"), label-maker Tuesday relabeling ("the font was wrong"),
  fixed breakfast ritual watching the G train surface.

## What this audit does NOT conclude
No territory is reassigned, no prompt is rewritten, no persona is declared
broken. Zen's WHY WE WRITE dip is a candidate explanation (implicit engine,
no stated motive, structure-heavy brief), not a diagnosis — confirming it
requires either the Phase 3 rewrite + re-test, or the same-source/four-
persona probe showing Zen specifically fails to produce an irreducible
reframe other personas could also produce. Maya's low article count has a
plausible mechanism (FORBIDDEN DEFAULTS + routing layer) but the downstream
cause (Fable override vs. draft quality vs. something else) isn't confirmed
from static text. Both are Phase 3 questions, not Phase 1.5 conclusions.

## Carried forward into Phase 3 (implementation, not now)
1. Delete/rewrite Siri's VOICE ANCHOR ownership clause (finding #1) —
   replace prohibition with affinity language.
2. Rewrite FORBIDDEN DEFAULTS (finding #2) from a blanket ban to something
   like "don't make ramp/curb-cut/lift your ONLY concrete example" — kills
   the laziest default without disabling Maya's real evidentiary register.
3. Replace the keyword→persona routing map (finding #3) with soft
   affinities + let Fable's own brief-writing (already persona-aware) carry
   more of the selection weight, OR audit why Fable-preferred reassignment
   away from Maya correlates with her low count.
4. Add one MOTIVE sentence per persona (all four missing, finding #5).
5. Surface Zen's and Pixel's implicit engines (drafted above) into an
   explicit one-sentence form the way Siri's already is; keep Maya's real
   engine (the promise-vs-Wednesday gap) but decouple it from the
   FORBIDDEN DEFAULTS collision.
6. Do NOT touch Siri's phenomenological engine, Maya's gap-attention, Zen's
   implicit measurement-limits engine, or Pixel's legibility-as-politics —
   all four are genuinely distinct and worth keeping; only the OWNERSHIP
   framing and the missing MOTIVE need to change.
