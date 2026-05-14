# Crip Minds v3.0 — Development Plan
*Written 2026-05-14. Based on full editorial audit of April–May 2026 output.*

---

## I. Diagnosis

The publication has outgrown its own template.

The orchestrator is more sophisticated than the output suggests. Six article types, five emotional registers, persona conflict vectors, beat tracking — all defined, mostly not working. The `standard` type dominates at 62%. The special forms exist but fire as louder essays, not as structurally distinct pieces.

**Six specific failure modes identified from reading all 35 April–May articles as a mainstream reader:**

| Problem | Root Cause | Reader Effect |
|---------|------------|---------------|
| Title monotony | No anti-pattern guard | 20/35 titles follow "The [Noun] [Something]" — archive reads as one author |
| Structural predictability | Single 5-step template | Reader anticipates every move by article 10 |
| Geographic narrowness | No diversity constraint | ~13/35 pieces grounded in Rotterdam |
| Citation exhaustion | No recency guard | Lefebvre ×4, Bateson ×3, Mike Oliver ×3 in one month |
| Topic clustering | Beat system not granular enough | NDIS ×3 in 16 days; "institution fails disabled person" ×15 in one month |
| Emotional flatness | `ecstatic` at 10%, lengths skewed short | 35 pieces of controlled analytical anger — no joy, no humor, no genuine surprise |

**What is NOT the problem:** model quality, individual article writing, the personas' intellectual depth. The raw material is good. The production system is running it through too narrow a channel.

**The shift from generative to reactive.** March / early April articles started from inside an obsession and pulled news in as evidence. Late April / May articles start from a news item and apply the disability angle. Both are valid. But the reactive mode, at daily cadence with a fixed template, produces a flatness the generative mode doesn't.

---

## II. Vision for v3.0

**Three words: range, distinctness, surprise.**

A daily reader should occasionally not know what they're getting. Five articles in a row should not feel like one article five times. The reader should be able to identify which persona wrote something without checking the byline.

v3.0 is not a redesign. It's a loosening of the constraints that calcified between March and May.

---

## III. Editorial Changes

### 3.1 New article type weights

Current: standard 62%, provocation 12%, fury 8%, confusion 8%, pleasure 7%, indefensible 3%.

New:

| Format | Weight | What it actually is |
|--------|--------|---------------------|
| `essay` | 35% | Current standard — news hook → anecdote → theory → close |
| `field_note` | 15% | 350–500w, present tense, one place/moment, no argument, ends mid-thought |
| `provocation` | 12% | One claim, one example, under 450w, structurally stricter — no resolution |
| `portrait` | 10% | One real named person, 1200w+, they're the subject not the example |
| `pleasure` | 8% | Body wants something specific, stays there, no disability-as-limitation framing |
| `fury` | 6% | Syntax breaks, short paragraphs, sentence fragments — structurally distinct from essay |
| `confusion` | 6% | Ends without resolution, no rescue conclusion |
| `indefensible` | 5% | Keep per-persona definitions, rotate more frequently |
| `series_part` | 3% | Explicitly continues a prior article, links to it |

### 3.2 Emotional register rebalancing

Current: wry 30%, clinical 25%, furious 20%, melancholic 15%, ecstatic 10%.

New: wry 25%, clinical 20%, **ecstatic 20%**, furious 15%, melancholic 15%, **celebratory 5%** (new — something was built right, won, or survived).

### 3.3 Geographic diversity rule

No city appears in consecutive articles by the same persona. Once every 4 articles, the anecdote comes from outside Western Europe/Australia.

**Expanded city pools per persona:**
- Pixel Nova: Tokyo, Lagos, São Paulo (+ existing Rotterdam/Amsterdam)
- Siri Sage: Osaka, Nairobi, Mexico City (+ existing Manchester/London)
- Maya Flux: Medellín, Accra, Seoul (+ existing Melbourne/Sheffield)
- Zen Circuit: Cape Town, Taipei, Montréal (+ existing London/Sheffield)

### 3.4 Citation freshness guard

Any theorist cited in the last 14 days is blocked. A `citation_ledger` table tracks appearances. Before generation: query last 14 days, inject **BLOCKED THEORISTS** list into prompt.

Target: Lefebvre, Bateson, Mike Oliver, Nick Walker, Georgina Kleege, Christine Sun Kim — each appears ≤2× per 30-day window.

### 3.5 Title rules overhaul

New instruction injected into every title generation:

> Do NOT begin with "The". Do NOT follow the pattern "The [Noun] [Verb/Prep] [Something]". Aim for titles that are specific enough to be impossible to reuse — a proper name, a number, a fragment, a question (rare), a single unexpected word. Recent patterns to avoid: "The Room Before the Room," "The Map That Ate the City," "The Sound of Mud."

### 3.6 Persona format ownership

Each persona owns one format that is structurally theirs:

- **Pixel Nova** owns `field_note` — shortest, most spatial, present-tense pieces
- **Siri Sage** owns `portrait` — the single-subject profiles
- **Maya Flux** owns `fury` — when syntax breaks it's Maya
- **Zen Circuit** owns `confusion` — unresolved essays

### 3.7 Cross-reference rule tightening

**Maximum one cross-persona reference per article.** It must introduce genuine disagreement that the article actually develops — not acknowledge and move past. Currently: "Siri Sage wrote about X, but here is where I diverge" followed by one paragraph that pivots away. New requirement: the disagreement must run for at least 150 words and remain unresolved at close.

### 3.8 Topic expansion

New angles to seed into `news_fetcher` extraction prompt and `article_ideas.md`:

- **What disability culture built** — crip art movements, D/deaf theatre, access riders as creative documents, crip humor traditions
- **Pleasure and the body** — what disabled people invented to experience pleasure the world didn't design for
- **Cross-disability friction** — when accessibility for one group works against another
- **Non-Western disability frameworks** — concepts outside the Anglo social model tradition
- **Speculative pieces** — not just critique of the present, but what a different arrangement would feel like

---

## IV. Technical Implementation

### 4.1 Citation ledger (new DB table)

```sql
CREATE TABLE IF NOT EXISTS citation_ledger (
    id       INTEGER PRIMARY KEY,
    date     TEXT NOT NULL,
    agent    TEXT NOT NULL,
    theorist TEXT NOT NULL,
    article_title TEXT
);
```

`_build_writing_prompt()` queries this, injects blocked list into prompt.

Auto-extract cited theorists from generated content using a post-generation pass (regex against known theorist name list).

### 4.2 Title anti-pattern injection

Add to prompt construction in `call_opus()`:

```python
TITLE_RULES = (
    "TITLE RULES:\n"
    "- Do NOT begin with 'The'\n"
    "- Do NOT follow pattern 'The [Noun] [Verb/Prep] [Something]'\n"
    "- Avoid: room, map, floor, sound, pattern, body as opening nouns\n"
    f"- Recent title structures to avoid: {recent_title_patterns}\n"
    "- Options: proper name, number, verb, fragment, question (rare)\n"
)
```

### 4.3 Geographic rotation

Each persona object gets `city_pool` list. New `persona_state` table tracks `last_city`, `city_cooldown_count`. City is injected into persona prompt as grounding location for the anecdote.

```sql
CREATE TABLE IF NOT EXISTS persona_state (
    agent        TEXT PRIMARY KEY,
    last_city    TEXT,
    city_history TEXT  -- JSON list of last 4 cities
);
```

### 4.4 Length distribution fix

```python
_LENGTHS = [
    (450,  0.10),   # field notes only
    (700,  0.20),   # provocations, short pieces  
    (950,  0.35),   # standard essays
    (1200, 0.25),   # longer essays
    (1600, 0.10),   # portraits, deep dives
]
```

`field_note` and `provocation` types get hard caps in their prompts (450w max).
`portrait` and `series_part` get hard minimums (1200w).

### 4.5 Feed source expansion

Add to `feeds.json`:
- Disability Arts Online (already present — verify active)
- Disability Visibility Project feed
- AfricaDisabled.com
- Krip-Hop Nation
- NIAD India
- Architecture/urban design: Dezeen (fix SSL error), Archinect, Metropolis
- International art criticism: Hyperallergic (already present), ArtReview, Frieze

### 4.6 Portrait subject database

New file: `automation/portrait_subjects.json` — seed with 30 real named disabled artists, writers, designers, theorists worth profiling. Siri Sage draws from this when `portrait` type fires.

Initial seeds: Evgen Bavčar, Lisette Schumacher, Carmen Papalia, Christine Sun Kim, Tarek Atoui, Sins Invalid collective, Alison Knowles, Pete Eckert, Alice Wong, Harriet McBryde Johnson (posthumous), Leah Lakshmi Piepzna-Samarasinha, Liz Jackson, El Gibbs, Sunaura Taylor.

---

## V. Migration Plan

Three phases. Each ships independently.

### Phase 1 — Fix the weights (1 day)
*No user-visible structural change, immediate tonal/format effect.*

- [ ] Fix `_ARTICLE_TYPES` weights (standard 62% → 35%)
- [ ] Fix `_REGISTERS` (ecstatic 10% → 20%, add celebratory 5%)
- [ ] Fix `_LENGTHS` distribution
- [ ] Add title anti-pattern instruction to prompt
- [ ] Add `citation_ledger` table + blocked theorist injection

Ship. Run 7 days. Assess.

### Phase 2 — Geographic diversity + persona sharpening (2–3 days)
*Visible voice differentiation, geographic range.*

- [ ] Add `city_pool` to each persona definition
- [ ] Add `persona_state` table + city rotation logic
- [ ] Assign format ownership per persona
- [ ] Tighten cross-reference rule (min 150w, must remain unresolved)
- [ ] Add new feeds to `feeds.json`
- [ ] Create `portrait_subjects.json`

Ship. Run 14 days. Assess.

### Phase 3 — New topics + series logic (3–4 days)
*Structural range, publication identity shift.*

- [ ] Add new topic angles to `news_fetcher` extraction prompt
- [ ] Add `series_part` article type with parent-slug linking
- [ ] Add `celebratory` register definition
- [ ] Expand `_INDEFENSIBLE_PROMPTS` with new vectors
- [ ] Update `_config.yml` version: **3.0**, codename: **TBD**
- [ ] Update `humans.txt` version history
- [ ] Update `PIPELINE.md` with new type/weight documentation

Ship.

---

## VI. What Stays the Same

- The four personas — intellectual DNA unchanged, only format ownership and city grounding changes
- Bregman writing style — sentence economy rules untouched
- News-grounded angle system — still starts from real news for most article types
- Bluesky/Tumblr/newsletter distribution pipeline
- Link pool injection system
- Jekyll site structure and frontmatter contract

---

## VII. Success Metrics

After 30 days of v3.0:

- No two consecutive articles share a title structure
- Rotterdam appears in ≤4 articles per 30-day window
- Lefebvre / Bateson / Mike Oliver appear ≤2× each per 30-day window
- ≥3 `field_note` articles per month (under 500w, present tense, no resolution)
- ≥2 `portrait` articles per month (single named subject, 1200w+)
- ≥2 non-essay formats per month with structurally distinct execution
- ≥1 article per week with a title that surprises
- At least one `celebratory` or `pleasure` piece per 2-week window

---

## VIII. Codename Candidates for v3.0

*(Pick one before Phase 3 ships)*

- **Scatter** — things thrown outward, not just argued
- **Counterweight** — balance after the monotone
- **Grain** — texture, variation, the thing that makes wood wood
- **Friction** — productive, not just resistant
- **Aperture** — opening, wider range of light
