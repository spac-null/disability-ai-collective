# Bregman anchor corpus — for register calibration, not for training

Standing reference for any future test/judge/tuning pass on the "read like Bregman"
effort (see `.claude/bregman-architecture-analysis.md` and
`.claude/bregman-write-economy-analysis.md` for the technique-level analysis this
complements). Built 2026-08-07. Short illustrative fragments only — full source
texts are copyrighted and not reproduced here; go to the original for anything
beyond a calibration snippet.

## Section 1 — ESSAY/REPORTAGE register (use these for anchor calibration)

This is the register cripminds personas should actually be matched against: Bregman
reporting something he found out, not persuading a live audience. All confirmed
consistent with each other across English and Dutch sources.

**Sources:**
- TED talk, "Poverty isn't a lack of character; it's a lack of cash" (2017)
- "The neoliberal era is ending. What comes next?", The Correspondent (2020)
- "The real Lord of the Flies", The Guardian (2020, excerpted from *Humankind*)
- *Utopia for Realists* / *Gratis geld voor iedereen*, ch. 1 (2016)
- *De geschiedenis van de vooruitgang*, Prologue (2013)
- *Het water komt* (2020)

**Confirmed shared habits (triangulated across all six sources):**
- Flat declarative opener, often very short ("Vroeger was alles slechter" — things
  used to be worse). No throat-clearing, no framework named before anything concrete
  happens.
- Abstract claim immediately followed by one concrete named source/study/statistic,
  never left as a bare thesis. ("A paper by a few American psychologists...";
  Spanish researchers, Nature, 464,411 songs, one number, one conclusion.)
- Real named people carry the argument, quoted directly and briefly — never "a
  researcher found," never a composite or unnamed authority.
- Verbatim-refrain repetition (a short list or phrase repeated word-for-word later
  in the piece) is a real device — distinct from wordplay, since nothing changes
  or twists between repetitions.
- Short "punch" sentences, sometimes just the repeated subject as its own sentence,
  for dramatic pause at a turning point ("Het water. Het water staat te hoog.").
- Sentence economy: short declarative → short declarative → payload. Lists run to
  three. One modifier, not three.
- Dates and places anchor every anecdote, including the author's own.
- Endings land on a plain fact, a real quote, or a concrete narrative beat — not a
  crafted twist or epigram.
- At most one named source developed at a time (a paragraph of context, then the
  quote, then its implication) before moving to the next — not stacked citations.

**What's essentially absent in this register** (confirmed by two independent
model-judged tests against real generated samples, 2026-08-07): metaphor standing
in for a plain mechanical fact, mirrored/cleft antithesis ("X is not Y, it is Z"),
aphoristic or ironic closers, sustained wordplay, treating an abstract framework —
or an inanimate object (a building, a drawing) — as a deliberate agent.

## Section 2 — ORATORY/LECTURE register (reference only — do NOT use for anchor calibration)

**Source:** The Reith Lectures 2025 with Rutger Bregman, Lecture 2 "How to start a
moral revolution" (BBC Radio 4, transcript, first 10 pages)

This is a *different register* and mixing it into Section 1's anchors would teach
the wrong lesson. A lecture is built to move a live audience toward a call to
action; cripminds personas write essays reporting what they found out, not stump
speeches. Confirmed present in this source, absent from Section 1:

- Sustained historical parallelism as a structuring device (explicitly drawing "just
  like Russia in 1917, just like the world today" across the whole piece).
- A named sequence of historical figures presented as a list to build momentum
  (three-in-a-row), the same shape flagged as a violation ("citation density") in
  Section 1's register.
- At least one genuinely aphoristic, quotable line built for the ear, not the
  page — a lecture is meant to produce a line that circulates afterward.
- Explicit rhetorical structuring announced to the audience ("I promised I'd
  structure this series as a classic three-part sermon").

**Takeaway:** Bregman's rhetorical intensity is register-dependent, not a fixed
personal style. Any future anchor-gathering should keep sourcing from his written
journalism/books, not his lectures or talks aimed at persuasion — even though both
are "real Bregman," they calibrate toward different, sometimes contradictory
targets.

## Section 3 — how to use this file

Two model-based repair strategies were tested against real flawed drafts on
2026-08-07 and neither broke through a real ceiling (both plateaued at 10-15
remaining issues per sample): rule-based repair (refined over 3 rounds) and
exemplar-based repair (shown Section 1's anchors directly, no rule list). Neither
beat the other consistently. That means this file's value is as a fixed,
reusable **judge reference** — for scoring/comparing future generation or repair
attempts consistently — not as a magic ingredient that fixes generation on its own
if fed to a writer or fixer model. See the "multi-draft-and-pick" and "dedicated
register-editor stage" ideas logged in this session's conversation for the more
promising next architectural moves; this corpus is what any of those approaches
would need as their fixed comparison target.

## Section 4 — considered and rejected: rigid 10-section essay template

2026-08-07, same session. An external document proposed a fixed structural
template for the whole essay: 10 named sections with specific word-count ranges
(Opening Scene 200-300w → Surprise → Zoom Out → Conventional Explanation →
Complication → Human Mechanism → Larger Principle → Present → Possibility →
Return, totaling 2500-4000w), mandating a scene-first opening and a coda-only
ending. Most of its individual techniques (historical-anecdote testing, human-
scale number translation, signpost phrases, expert disagreement) duplicated what
was already in the generation prompt or got added to it the same session — no
extraction needed there.

**The structural mandate itself was rejected, not adopted.** It directly
contradicts two rules already deliberately built into this pipeline:
"OPENING — NO FIXED SHAPE" (explicitly bans defaulting to a scene-first open —
"the placed-body-in-a-named-room-in-present-tense move is now overused") and
"ENDING — NO FIXED SHAPE" (offers five valid endings specifically so no piece is
forced into one shape). Rule 27 already states the underlying reasoning: these
structural moves "were reverse-engineered from finished work; adding them by
hand is what makes a draft read as technique-shaped with nothing reported inside
it." A fill-in-the-blanks 10-section formula is exactly that failure mode. It
would also break the existing length/type variety system (450-2800 word buckets;
field_note/portrait/essay/provocation each structurally different) since one
rigid 2500-4000w template doesn't fit any bucket except the longest.

If this template (or something like it) gets proposed again in a future session:
it's already been evaluated and rejected for this specific reason, not
overlooked.

**2026-08-07, later same day — second, larger document in the same family
reviewed.** Same rigid macro/micro-structure mandate (an 11-section version this
time), same rejection applies, no need to re-litigate. Two genuinely new items
extracted and shipped: a corporate/journalese cliché ban (tip of the iceberg,
perfect storm, wake-up call, etc. — a different register than the existing
academic-jargon list) and a "no empty grandeur" rule (don't gesture at stakes
without specifying them). One claim explicitly NOT adopted: a precise sentence-
length distribution (60-70% short-medium / 20-30% longer / 5-10% very short)
with no shown basis — reads as an invented-sounding statistic, and baking an
unverified one into the rules meant to prevent invented statistics would be a
bad joke. One idea logged as a separate, untested technique rather than a style
rule: a "private pre-draft workflow" (silently draft thesis/evidence/mechanism
before writing the visible essay) — genuine chain-of-thought scaffolding, worth
a real test on its own terms later, not something to insert blind alongside the
sentence-level rules.

**2026-08-07, later same day — third document, different in kind.** Not a
rigid essay template; a statistical/corpus-linguistics framework proposing to
model sentence-length distribution, function-word frequency, and n-gram overlap
rather than copying phrases or mandating structure. Genuinely different
methodology from the two rejected documents, evaluated on its own terms.

Verified its central numeric claim against real data instead of trusting or
dismissing it: computed real sentence-length stats from all 919 sentences
across the three Dutch books in Section 1 (Het water komt, De geschiedenis van
de vooruitgang, Gratis geld voor iedereen). The document's claimed distribution
(15% <=8 words / 45% 9-18 / 30% 19-30 / 10% 31-45) was directionally right but
not accurate — real measured: 24.4% / 43.3% / 23.4% / 5.5%, mean 16.6, stdev
12.6. Same lesson as the earlier document's invented 60-70/20-30/5-10 claim:
check before trusting a confident-sounding number, even when the direction is
plausible.

Three real extractions shipped from this document:
1. Fixed a genuine ambiguity in the MIRRORED/CLEFT SENTENCE ban (R15b/R16b) —
   it risked suppressing the already-protected REDEFINE technique ("not X, but
   Y" corrections use nearly the same surface pattern as the banned
   symmetrical-mirroring tic). Now explicitly distinguished in all three rule
   locations.
2. END-WEIGHT — strongest/newest information goes at the end of the sentence.
   Real, standard principle, not previously encoded.
3. A genuinely new deterministic check (RSD, sentence-length distribution) —
   built on the REAL measured baseline above, not the document's claimed one.
   Flags suspiciously uniform sentence rhythm (near-zero stdev, zero short
   sentences, high mean length) as its own axis, independent of every pattern-
   based check already shipped. This is the first check in the whole session
   that tests distribution rather than pattern-matching a specific violation.

The document's Dutch-specific lexical content (sections 1, 3-47: Dutch
connective words, Dutch verb lists, Dutch sentence archetypes) doesn't transfer
to this pipeline's English output and wasn't used — noted for completeness in
case Dutch-language generation is ever added elsewhere in this project.

## Section 5 — direct excerpt review, 2026-08-09 (publisher-licensed use confirmed for this repo)

Triggered by a real reader complaint about a live article's opening sentence
("A ramp is a promise the ground makes" — textbook inanimate-object-as-agent).
Investigation found the rule that bans this had already fired correctly in
the pre-commit gate and was overridden by an unrelated threshold (a single
register violation didn't meet the 3-violations-needed bar — fixed separately,
see production_orchestrator.py git log 2026-08-09). While diagnosing this, the
site owner supplied three real excerpts directly for comparison, confirming
two things the corpus already had right and surfacing two genuine gaps.

**Sources supplied:** *De geschiedenis van de vooruitgang* / *Utopia for
Realists*, ch. 1 opening ("De terugkeer van de utopie" / "Twee eeuwen van
waanzinnige vooruitgang"); *Het water komt*, ch. 1 opening ("Beste
landgenoot"). Both already represented in Section 1's source list; this
entry adds specific technique findings the earlier pass didn't capture.

**Confirmed, matching what's already logged above:**
- The exact short-punch-sentence example already quoted in Section 1 ("Het
  water. Het water staat te hoog.") is from this same chapter opening —
  direct confirmation the earlier analysis was reading the real thing.
- Verbatim-refrain repetition, confirmed a second time: the seven-word list
  "arm, hongerig, bang, vies, dom, ziek en lelijk" (poor, hungry, afraid,
  dirty, stupid, sick, ugly) opens the chapter and recurs word-for-word at
  the chapter's close, unchanged.

**Two genuine gaps found and fixed (see this same repo's git history,
2026-08-09, for the actual rule-text patches — four duplicate LIST-length
rule locations and three duplicate METAPHOR-FOR-MECHANISM rule locations):**

1. **List length is earned, not flat-capped.** The "utopia" excerpt's second
   paragraph lists nine items in one sentence — Columbus, Galileo, Newton,
   the scientific revolution, the reformation, the enlightenment, gunpowder,
   the printing press, the steam engine — immediately followed by the
   punchline that income was still exactly what it had been six hundred
   years earlier. This directly contradicts the flat "4+ items is always a
   violation" rule that existed everywhere in this pipeline. The real
   pattern: a long list is earned when the very next sentence cashes it in
   with a payoff or reversal; a long list with nothing after it is still the
   violation the rule was right to ban. (Confirming the cap's basic
   instinct isn't wrong, either — the same excerpt elsewhere keeps a
   national-character list to exactly four items: "lukt niet, mag niet, kan
   niet" plus one more, no payoff sentence needed because it's not building
   to a reversal.)

2. **A metaphor inside a real quote is not the writer inventing an image.**
   The "Het water komt" excerpt closes its opening section on a real letter
   Johan van Veen wrote to a British friend after the 1953 flood: "Niet een
   kameel, maar een hele kudde olifanten ging door het oog van de naald" —
   not one camel, but a whole herd of elephants went through the eye of the
   needle. That's figurative language, but it's a real, documented, directly
   quoted sentence from a real historical person's real letter — not the
   narrator reaching for an invented image to describe a mechanism, which is
   what the METAPHOR FOR MECHANISM rule was actually built to catch. The
   rule as written before this fix didn't distinguish the two cases and
   would have flagged a persona correctly quoting a real source's own
   metaphor. Fixed to exempt metaphors inside real, attributed quotes
   specifically.

**Process note:** both fixes came from a reader comparing a live article
directly against real source text, not from testing against this corpus
file's own summarized bullet points. The summarized rules are useful as an
operational rule-of-thumb but are a lossy compression of the real thing —
periodically re-checking the rules against fresh excerpts (as happened here)
is how gaps like these get caught; the summary alone wouldn't have surfaced
either one.

## Section 6 — architecture migration + weekly full audit, 2026-08-09

Same-day follow-through on Section 5's fixes, expanded into a full-day
architecture pass. Summary for future sessions picking this up — full detail
is in git log (commits from `168ee79` through `66663d7` on this date):

**Module split (DONE).** `automation/production_orchestrator.py` went from
6,101 lines / ~95 methods / one class to 186 lines. Every method moved
verbatim into 11 mixin files under `automation/orchestrator/` (config,
personas, debate, images, publish, gate, llm, discovery, content_checks,
fact_check, review, social, generate), composed via multiple inheritance —
zero behavior change, every `self.x` reference resolves the same regardless
of which file defines the method. Two real bugs caught before shipping by
a full AST unresolved-name scan (not just eyeballing): a missing
`import random`, and a `Path(__file__).parent`-based path that would have
silently resolved to the wrong directory once relocated (same bug class
caught twice — also in `config.py`'s `_SCRIPT_DIR`). A `snapshot_test.py`
harness was built first specifically to make "the method body didn't
change" a verified claim rather than an eyeball one, on a pipeline with
zero other test coverage that publishes live and unattended.

**Rule-text convergence (substantially DONE).** Every rule in
`style_rules.py`'s registry was checked for (a) presence/absence across the
`GATE`/`GENERATE`/`REVIEW` stages the registry itself declares, and (b) exact
wording drift between `gate.py`/`review.py`/`generate.py`/the registry.
Real fixes shipped: `system-voice` was completely absent from the blocking
gate despite the registry's own rationale field already saying it had been
"moved to BLOCKING" (the text just never got added); `meta-language-
commentary` and `stacked-temporal-clauses` existed ONLY in the registry with
zero real wiring anywhere; `front-loaded-sentence` was missing its worked
examples in the gate; `crafted-rhetoric`'s plain-comparison exemption was
missing entirely from the writer prompt (a real behavior risk — the writer
could over-avoid harmless comparisons with nothing telling it not to);
`decoding-required`'s registry text was itself stale, missing a worked
example the live code already had correctly (the one case this round where
code was ahead of the registry, not behind it). Confirmed clean or
correct-by-design: `long-list`, `paragraph-length`, `section-breaks`,
`vague-we`, `named-references`, `subject-verb-distance`, `ending-shape`,
`jargon`, `nominalization`.

**Shadow-mode checks (3 shipped, IN OBSERVATION — do not act before
2026-08-23).** New deterministic checks for writer-prompt rules with zero
downstream enforcement, added to `review.py`'s advisory sidecar only, never
blocking: bullet points/numbered lists in body, the two FORBIDDEN word lists
(academic jargon, corporate/journalese clichés), and truncated endings (a
real silent-failure risk given several LLM calls run under a `max_tokens`
cap). Two candidates were checked and correctly rejected rather than forced:
`FORBIDDEN DEFAULTS` (bans something being the *central* argument, not mere
presence — a naive match would flag any incidental mention) and `FORBIDDEN
REFERENCES` (already has real enforcement via `_get_recent_references`
feeding into the generation prompt directly, no gap to fill).

**This weekly audit (2026-08-09, same day as the work above — the first
audit under the `.loop_last_full_review` tracking convention).** Checked
for: duplicate/mislabeled R-numbers in `GATE_SYSTEM`/`RULES_SYSTEM` (none —
sequential 1-17 and 1-19), whether the register-escalation logic
(`register_prefixes` in `gate.py`) needed updating for the newly-added R16/
R17 rules (checked and confirmed it correctly excludes both — `system-voice`
is deliberately classified as a "mechanical, isolated, patchable" violation
per a real 2026-08-07 validation test, not a "pervasive register" one; almost
"fixed" this before reading the existing comment's reasoning, which was
right), whether `check_rule_drift.py`'s file-glob would pick up future new
orchestrator files (confirmed yes, no hardcoded list), and a scan for
leftover TODO/FIXME comments (none — one grep hit was a false positive on
the substring "TOKEN" inside `MASTODON_ACCESS_TOKEN`). **No new issues
found.** A clean audit is itself the useful signal here — confirms the
day's incremental work didn't leave anything half-wired behind it.

**Next weekly audit due:** ~2026-08-16. Check `automation/.loop_last_full_review`
for the actual last-run date before assuming this one still applies.

## Section 7 — anchor-architecture blueprint: design findings not captured elsewhere (2026-08-09)

The anchor-architecture blueprint itself (Stages 0-G, tracked in
`.claude/audience-engagement-tasklist.md`'s addendum) was produced by a large
Opus design agent in this session's transcript — no standalone blueprint
document was ever committed. These specific findings from that agent's
report didn't make it into the tasklist summary and would otherwise only
exist in conversation history. Recorded here so they survive session
boundaries.

**Fabrication-vector constraint, required for Stage D/E when built.** An
"anchor" (a person/object/place a Stage-D brief would commit to and the
writer would return to 3+ times) is a *worse* fabrication risk than a normal
one-off invented detail — an invented anchor gets repeated and reinforced
across the piece instead of appearing once, and it's exactly the kind of
confident-sounding, load-bearing detail the fact-checker is least likely to
flag on a first pass (see `automation/orchestrator/generate.py:548`'s
existing "NO INVENTED STATISTICS" rule for the closest existing analogue —
no equivalent rule exists yet for a *named anchor*). Whoever builds Stage D's
brief-generation prompt and Stage E's writer-prompt block must explicitly
require the anchor be something real and locatable — sourced from the
article's actual research material, not invented to fit a device — the same
way statistics are already required to be real. This is not optional
polish; skipping it turns the anchor mechanism into a fabrication amplifier.

**Stage A measurement methodology (scripts never committed, note it here so
a future re-run isn't starting from zero).** The 88%/26%/10-15% figures in
the tasklist came from two successively refined ad-hoc scripts, run inline
during the design agent's session and never saved to the repo — there is no
`measure_anchors.py` or similar to inspect or extend. What's known about
their methodology, for reconstruction if this is ever revisited:
- **First pass (88%, would have killed the project):** naive — flagged any
  proper noun recurring in >=3 paragraphs of an article, no filtering.
- **Second pass (26%, the number the tasklist currently relies on):** added
  a larger stopword/blocklist, required confirmed non-sentence-initial
  occurrences (to exclude a name that's just the grammatical subject
  repeatedly, not a deliberate callback), and multi-word phrase matching
  (not just single proper nouns). Of that 26%, roughly half was judged
  topical necessity (an article about Deaf culture saying "Deaf" often isn't
  a device) rather than a deliberate anchor — hence the "real device rate
  10-15%" estimate.
- **A third, more rigorous pass (100 articles, hand-checked against a human
  judgment of "is this actually a Bregman-style anchor," not just a keyword
  detector) was proposed in conversation but never run.** If Stage A's
  number is ever load-bearing for a bigger decision, this is the gap to
  close first — the current 26%/10-15% figures rest on scripts nobody can
  currently inspect.

**Known gap in the pipeline's own safety net: `snapshot_test.py` doesn't
cover `generate.py`.** Confirmed by reading `automation/snapshot_test.py`
directly — `_snapshot_llm_calls` only exercises `_pre_commit_gate` (gate.py)
and `validate_article` (review.py). It never imports or calls anything from
`generate.py` — no `_run_production_automation_locked`, no
`_fable_editorial_brief`, no writer-prompt construction. This means Stage
D/E, whenever built, will be the first change to the writer prompt with zero
snapshot-test coverage protecting it. Worth closing before Stage E ships,
not after.

**Rewrite-pass / plan-following conflation risk — relevant to interpreting
Stage B calibration data.** `rewrite_with_opus`/`_fable_polish_rewrite`
(`generate.py`, lines ~661-692) run during generation, *before*
`_plan_follow_read` (`review.py`, wired into `validate_article`) ever checks
whether the plan (`opening_shape`/`correction_moment`/`resisting_example`)
was actually executed. A plan-following failure introduced by the rewrite
pass and one present in the original draft are currently indistinguishable
to the check. This matters once real calibration data starts accumulating
(see tasklist Stage B): a low agreement rate could mean the judge itself is
wrong, or it could mean the rewrite pass is silently undoing a plan the
first draft executed correctly — two very different fixes, and nothing
today can tell them apart. Worth instrumenting (e.g. running
`_plan_follow_read` before and after the rewrite pass) before trusting any
conclusion drawn from low agreement.

**Refrain instruction (Stage D/E) plausibly conflicts with an existing
crafted-rhetoric ban — unreconciled.** `gate.py`'s CRAFTED RHETORIC rule
(R15, clause on "aphoristic or ironic closers") bans a piece ending on a
crafted twist rather than a plain fact, quote, or concrete narrative beat.
A refrain that echoes an opening phrase near the ending is a plausible match
for exactly this ban. The pipeline already has one narrow carve-out —
`generate.py:540`, "a plain list can repeat verbatim as a refrain" — but
that only exempts repeating a stated *list*, not an opening *phrase*. No
equivalent exemption exists for a phrase-refrain. Moot until Stage D/E has
code, but whoever builds it needs to either extend the carve-out or accept
that a refrain instruction will regularly collide with an existing blocking
rule.
