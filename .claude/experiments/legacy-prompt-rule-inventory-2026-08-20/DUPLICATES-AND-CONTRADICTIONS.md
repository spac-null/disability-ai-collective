# Duplicates and Contradictions

Matrix cells below were computed by substring-matching the **actual** prompt strings
(AST-extracted literals for the static ones, captured assembled text for the writer),
not read off by eye.

---

## 1. Duplication matrix

Five places a style rule can live:
**WRITER** = `generate.py:783` prompt · **REWRITE** = `llm.py:394` SYSTEM ·
**GATE** = `gate.py:233` GATE_SYSTEM (blocking) · **REVIEW** = `review.py:1173`
RULES_SYSTEM (advisory) · **REGISTRY** = `style_rules.py` RULES (**dead — no consumer**)

| Family | WRITER | REWRITE | GATE | REVIEW | REGISTRY | Copies |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| JARGON | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| NOMINALIZATION | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| SYSTEM VOICE | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| VAGUE WE | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| FRONT-LOADED SENTENCE | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| LONG LIST / LISTS OF THREE | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| PARAGRAPH LENGTH | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| SECTION BREAKS | ✔ | ✔ | ✔ | ✔ | ✔ | **5** |
| NAMED REFERENCES | ✔ | ✔ | — | ✔ | ✔ | 4 |
| NO DECODING REQUIRED | ✔ | ✔ | — | ✔ | ✔ | 4 |
| CRAFTED RHETORIC | ✔ | — | ✔ | ✔ | ✔ | 4 |
| ONE IDEA PER SENTENCE | ✔ | — | ✔ | ✔ | ✔ | 4 |
| ENDING SHAPE | ✔ | ✔ | — | ✔ | ✔ | 4 |
| INLINE DEFINITIONS | ✔ | ✔ | ✔ | ✔ | — | 4 |
| PLAIN VOCABULARY / LATINATE | ✔ | ✔ | ✔ | ✔ | — | 4 |
| ONE MODIFIER PER NOUN | ✔ | ✔ | ✔ | ✔ | — | 4 |
| SUBJECT-VERB DISTANCE | — | — | ✔ | ✔ | ✔ | 3 |
| META-LANGUAGE COMMENTARY | ✔ | — | — | ✔ | ✔ | 3 |
| STACKED TEMPORAL CLAUSES | ✔ | — | — | ✔ | ✔ | 3 |

**8 families exist in all five places. 16 exist in four or more. 19 in three or more.**

### Primary owner per duplicated family

| Family | Primary owner should be | Redundant copies | Duplication class |
|---|---|---|---|
| All 8 five-copy families | **GATE** (it is the only blocking enforcement) | WRITER (instruction), REWRITE, REVIEW, REGISTRY | **CONFUSING** — the writer copy is arguably legitimate (generative instruction ≠ check), the REVIEW copy is a second judge with a different number scheme, the REGISTRY copy is dead |
| CRAFTED RHETORIC | GATE (R15, 2,000+ ch of worked exceptions) | WRITER, REVIEW, REGISTRY | **RISKY** — the exception carve-outs (quoted-speech metaphor exemption, `not X but Y` protection) are stated at different lengths in each copy; a fix to one does not propagate |
| ENDING SHAPE | WRITER + REVIEW R11 | REWRITE 7 + 25 | **HARMLESS** — verified consistent: all three enumerate the same five valid shapes and the same ban list |
| PLAIN VOCABULARY | one owner needed | **also duplicated *inside* the writer prompt itself** — lines 91 and 113 of the assembled prompt, two different texts under the same header | **CONFUSING** |

### Numbering divergence — the exact bug class `style_rules.py` was built to prevent

`style_rules.py`'s header states R-numbers are never stored, and are assigned at render
time from stable slugs, "what makes the R14-means-something-different-in-two-functions
class of bug structurally impossible going forward." Because the registry was never
wired in, the hand-typed numbers survive and still collide:

| Rule | GATE number | REVIEW number |
|---|---|---|
| VAGUE WE | R5 | R6 |
| SYSTEM VOICE | R17 | R5 |
| CRAFTED RHETORIC | R15 | R16 |
| ONE IDEA PER SENTENCE | R16 | R17 |
| FRONT-LOADED SENTENCE | R6 | R7 |
| LONG LIST | R8 | R10 |
| PARAGRAPH LENGTH | R7 | R8 |
| JARGON | R10 | R13 |
| SUBJECT-VERB DISTANCE | R14 | R15 |

`gate.py` has `_parse_rule_verdicts` / `_missing_rule_ids` keying on these numbers. A
"R5 violation" means SYSTEM VOICE in one file and VAGUE WE in the other.

---

## 2. Contradictions

Severity: **HIGH** = actively shapes live output in a direction current architecture
rejects. **MEDIUM** = live but partially mitigated. **KNOWN-DIVERGENCE** = real conflict,
already documented as deliberate.

### C1 — Testimony quota survives in the rewriter — **HIGH, LIVE, UNDOCUMENTED**

AR3 (`.claude/experiments/artistic-reset-ar3-unforced-human-presence-2026-08-17.md`,
released as AR3A, commit `3225ea1`) removed the testimony quota from the writer prompt
and replaced it with:

> `HUMAN TESTIMONY / NAMED VOICES: … Zero testimony is valid. Zero quotations is valid.
> Zero secondary named people is valid.` — `generate.py:882`

**`llm.py`'s `rewrite_with_opus` SYSTEM still contains both removed blocks:**

> `33. NAMED VOICES: The draft should have 2-3 real named people … **REQUIRED**: beyond
> the primary subject of the article, a second real named person must appear doing
> something specific in the body.`
>
> `33b. SOMEONE ELSE MUST SPEAK: at least one other person must say something out loud
> inside actual quotation marks, in the past tense…`

`rewrite_with_opus` is called on every production article at `generate.py:1168`.
Confirmed by grep: `"SOMEONE ELSE MUST SPEAK"` occurs **0 times** in `generate.py`,
**0** in `review.py`, **1** in `llm.py`.

The AR3A release note in `LOGBOOK.md` records checking `style_rules.py` and `gate.py`
for surviving copies. `llm.py` was not checked.

**Partial mitigation, stated precisely so this is not overclaimed:** rule 33b ends
"If the draft has none, say so in the edit — but do not invent a quote; never attribute
words to a real named person that were not in the draft," and
`_reject_if_unsupported_specifics` runs on the rewrite output. So the direct fabrication
path is guarded. What is **not** removed is the editorial pressure AR3 identified as the
cause — the rewriter is still told the draft is deficient without a second named voice.

### C2 — Thesis placement — **HIGH, LIVE, ALREADY QUEUED AS AR3.1**

Same model call receives both:

- SYSTEM (`llm.py:232`): "strong thesis from sentence one"
- USER (`generate.py:889`): "One thesis the whole essay serves — **but never state it**.
  … If you write `My thesis is` or `I argue that` or `This essay will show` — delete it."

Already identified and queued as AR3.1 in `LOGBOOK.md`; recorded here for completeness
because it is still live.

### C3 — Persona canon injected twice, with self-contradicting framing — **HIGH, LIVE, UNDOCUMENTED**

In the assembled writer prompt for a **fictional** persona (Maya Flux, Siri Sage,
Zen Circuit):

- lines 14–59: `--- YOUR CANON (WHO YOU ARE, IMMUTABLY) ---` + 7,216 chars
- lines 201–248: `--- AUTHORIZED PERSONAL HISTORY ---` + **the same 7,216 chars,
  SHA-256 identical** (`4324a24e04071304…`)
- line 250, joining them: "Your editorial CANON above tells you how to think and write …
  **It does NOT authorize autobiographical facts.**" — immediately after a block that
  *is* that same canon text, presented as the authorized factual history.

The prompt therefore tells the writer that text X is not factual authority and that
text X is the only factual authority, ~190 lines apart.

**Root cause** (`llm.py:589 _load_persona_factual_context`): personas without a
`<slug>-factual.md` fall back to `_load_persona_canon()` in full. That fallback is
deliberate and well-argued in its docstring for *provenance* purposes. The
*prompt-assembly* consequence — verbatim duplication plus the contradictory joining
sentence — is not addressed anywhere in the code or docs.

**Not a problem for Pixel Nova:** the two blocks correctly differ (5,903 vs 3,647 chars,
different hashes), because `pixel-nova-factual.md` exists and only its
`## AUTHORIZED FACTUAL CONTEXT` section is extracted.

**Cost:** 7,216 wasted characters (~12% of the writer prompt) for 3 of 4 personas.

### C4 — SOFA `Byline ≠ prose persona` vs live persona roleplay — **KNOWN-DIVERGENCE**

`SOFA-METHOD.md` §4: "The writer must not roleplay disability, imitate supposed
autistic/Deaf/mobility/neurodivergent sentence patterns, insert biography as credential,
or write 'in character' because the byline is a persona. **Byline ≠ prose persona.**"

Live writer prompt opens `YOU ARE MAYA FLUX. Mobility disability.` followed by
`WRITE LIKE THIS PERSON`, `YOUR WOUND`, `YOUR LIFE`, and canon ×2.

**This is a documented divergence, not an accident.** `SOFA-METHOD.md`'s own SCOPE block
states: "**Production has NOT migrated to Article Form.** No Sofa/Article Form
implementation is deployed. Live production runs the older Fable/persona/writer
pipeline." Listed so the inventory is complete, not as a new discovery.

### C5 — SOFA "no persona subject territory" vs `_AGENT_BEATS` — **MEDIUM, LIVE**

`SOFA-METHOD.md` §2: "Do not treat any persona as owning a subject territory
(mobility ≠ transportation stories, Deaf ≠ communication stories, etc.)."

`config.py:258` `_AGENT_BEATS` assigns exactly that: `Maya Flux → urban-mobility,
disability-economics, care-as-design, protest-history`. `_get_beat_nudge` then injects
`BEAT NOTE: You haven't written about urban mobility recently — if this topic connects,
explore that angle.` into the live writer prompt (present in the captured Maya prompt,
line 252).

Same documented-divergence caveat as C4, but flagged separately because the beats table
is *actively steering* topic selection now, and is a smaller, independently removable
piece than the whole persona architecture.

### C6 — Paragraph length: SOFA vs writer vs blocking gate — **MEDIUM, LIVE**

| Source | Instruction |
|---|---|
| `SOFA-METHOD.md` §10 | "Prefer: **developed paragraphs** … Avoid: staccato simplification" |
| Writer prompt | "Keep paragraphs short. **Two to four sentences is the target.** If a paragraph exceeds five sentences, it is trying to do two things; break it" |
| GATE R7 (**blocking**) | "LONG PARAGRAPH — more than 5 sentences in one paragraph" |
| REVIEW R8 | "flag any paragraph exceeding 5 sentences" |
| REWRITE 23 | "2 to 4 sentences as the norm … The rule is not variety — it is compression" |

Direct opposition on one measurable variable. The canonical method asks for developed
paragraphs; a blocking production gate rejects them. This one is **not** covered by the
"production hasn't migrated" caveat in the same way C4/C5 are — paragraph development is
a §10 Writing Standard, not part of the Discovery→Form→Writer staging that
`SOFA-METHOD.md` marks as unmigrated hypothesis.

### C7 — `PLAIN VOCABULARY` stated twice, differently, inside one prompt — **LOW, LIVE**

Assembled writer prompt line 91: "PLAIN VOCABULARY: Plain English only. Use not utilise…
When you must use a technical term, unpack it immediately in the same or next sentence."
Line 113: "PLAIN VOCABULARY. Prefer the Anglo-Saxon word over the Latinate one…
Keep technical terms only when no plain word carries the same precision — earn them one
at a time."

The second says earn technical terms sparingly; the first says unpack them immediately.
Compatible in spirit, divergent in instruction, and both under an identical header 22
lines apart.

### C8 — `style_rules.py` claims authority it does not have — **MEDIUM, DOCUMENTATION**

The module docstring and `.claude/CONTEXT.md:81` both describe it as the "single source
of truth for the Crip Minds writing-style rules." It is not wired to anything. Any future
work that edits a rule there and believes it has changed production behaviour will be
wrong. This is a live trap for the next person, including a future agent session.

---

## 3. Negative-prohibition risk (Edinburgh class)

Edinburgh showed negative Form instructions can surface as positive prose claims. The
live writer prompt contains **80 negative-prohibition tokens** (`Never` 18, `never` 19,
`Do not`/`do not`/`Do NOT` 29, `BANNED` 6, `banned` 5, `FORBIDDEN` 3).

Highest-risk instances — negative rules that carry concrete nouns, names, or verbatim
sentences a model can echo:

| Rule | Payload it puts in the context window |
|---|---|
| `FORBIDDEN DEFAULTS` | "ramp, curb cut, grab rail, tactile paving, accessible toilet, lift" — the exact objects the piece must not centre |
| `TITLE RULES` | "room, map, floor, sound, pattern, body, wall, door, city, space" — banned opening nouns, plus a list of recent real titles |
| `BLOCKED THEORISTS` | real theorist names, injected only to forbid them |
| `'ARGUMENT' — NEAR-ZERO` | a corpus statistic about CripMinds itself: "appears in 63 of 138 published articles (119 total uses)" |
| `ONE IDEA PER SENTENCE` | a full verbatim published bad sentence ("A building whose entire public character is a colour scheme has decided, before the concrete is poured…") |
| `NO SIGNPOSTING` | four verbatim banned signpost phrases |
| `NO ENCYCLOPEDIC APPOSITIVES` | "ICML, a major machine learning conference", "the Wiener Werkstätte, an influential Austrian design workshop" |

GATE_SYSTEM R15 alone carries ~2,000 characters of quoted bad examples, and REVIEW
RULES_SYSTEM repeats many of them.

**This is an observation about surface area, not a measured failure.** No experiment was
run and none should be. It is recorded because the owner named negative prohibitions as
the priority inspection target, and this is where they are concentrated.
