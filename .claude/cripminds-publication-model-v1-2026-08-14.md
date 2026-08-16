# CripMinds Publication Model V1 — Synthesis After Format Lab V0–V2 — 2026-08-14

Branch: `publication-model-v1-2026-08-14`
Worktree: `~/code/disability-collective-ai-publication-model-v1`
Based on: `format-lab-v2-what-the-room-heard-2026-08-14` @ `40dd5af`
Production: `origin/main` @ `7a367f4` — untouched

This is synthesis, not another prototype. Nothing in this document is implemented. It draws
only on what V0, V1, and V2 actually documented and decided — re-read in full for this pass,
not recalled from memory.

---

## Format Lab evidence (extracted, not summarized)

### V0 — Temporal Gap / "The Room Moves On" (F1 — Form Lab validated)

What prose could not do: state a delay ("captions lag by several seconds"), but not
reproduce the *felt sequencing* of holding a reaction in front of you — applause, a shout —
while its cause is still six seconds from arriving. Removing the ordering mechanism removed
the argument entirely (the gimmick test the whole model below is built on). The mechanism
generalized past disability: mediation can separate correctness from presence for *anyone*,
not just a caption-dependent reader — an anti-essentialism finding, not a caveat.

Equally important, and easy to undercount: **testing itself surfaced a real defect** (the
interactive controls stayed visible-but-dead with JavaScript off) that no amount of design
review caught. V0 is the first evidence that this model's quality claims must be verified by
actually running the work, not asserted from the build.

### V1 — Generative Media Affordance Pass (G2 — some classes justified, generative
production stays selective)

- **Form ≠ medium ≠ generative technology** is a real, load-bearing three-way distinction, not
  a rhetorical flourish — demonstrated by the many-to-many Format↔Media map (e.g., The Loop
  realizable through archival footage, generated video, hand illustration, or CSS animation,
  with the mechanism unchanged across all four).
- **Deterministic, hand-authored, or signal-processing tools consistently outperformed
  generative ones on the two criteria that matter most to CripMinds' actual working method:
  control and temporal precision.** This is a convergent finding, not a single data point — it
  showed up independently in the V0 control analysis (reasoning about V0's own subject) *and*
  in Stage B's separate, later, cross-vendor tool research (arXiv 2510.02226 on video timing
  degradation; three.js/`model-viewer` beating generative 3D on exact control).
- **Provenance signals do not survive the real distribution path.** C2PA/SynthID are now
  broadly adopted (6,000+-member coalition as of this research), but are routinely stripped by
  social platforms on upload — meaning CripMinds' own on-page disclosure is the only
  dependable provenance layer, not vendor watermarking. This is a documented 2026 finding, not
  a hypothetical risk.
- **The four-class ontology (Document/Reconstruction/Simulation/Generated Interpretation)
  survived a stress test but needed refinement toward compound, per-component labeling** —
  real composite objects (an outpainted photo, a generated voice reading a real quote) mix
  classes within one artifact; V1 recommended this refinement but did not test it against a
  real build.
- **All three concretely-designed future works (D, E, F) independently converged on
  non-generative approaches as their strongest version.** This is presented in V1 itself as
  "not a hedge... the honest result of applying CripMinds' actual constraints... to genuinely
  promising subjects" — a finding, not an absence of imagination.

### V2 — "What the Room Heard" (M1 — multimodal form validated) — the actual result, not an
assumed success

V2's decision was M1, but the evidence for it is specific, and worth stating precisely rather
than reflexively: the on-page, falsifiable claim is that **the entry point a reader chooses
first tends to feel authoritative even when it structurally isn't** — demonstrated by
building three independent, honest, non-generative renderings of one real 10.31-second
public-domain recording and finding they genuinely diverge (a flat block of bars vs. jagged
ones; an explicit "unverified" flag next to an otherwise confident-sounding log). The gimmick
test passed: keeping only one rendering removes the argument, leaving "just a fact about one
recording."

Three findings from V2 are load-bearing for this synthesis specifically, because they were
*tested*, not merely reasoned about in the abstract:

1. **The provenance ontology needed per-component labeling in an actual build**, not only in
   V1's design-only stress test — the text log itself needed two different labels for two
   different claims *within itself* (timing = Document-grade, topic paraphrase = explicitly
   unverified). This confirms V1's recommendation with real evidence rather than repeating it.
2. **Media lineage's meaning-preserving/meaning-consequential distinction held up against a
   real transformation chain**, including a genuine, disclosed analytical choice (why −35dB,
   why a 0.3s merge window) that had to be defended as reasonable rather than merely
   mechanical.
3. **Testing caught two real, generalizable defects**, not just V2-specific bugs: (a) a
   reader-ordering assumption that broke when the reader picked a non-default entry point, and
   (b) a permanently-unreachable section caused by hardcoding `hidden` in static markup instead
   of setting it from script. Both are QA lessons for *any* future non-article work, not
   incidental fixes to this one page.

### Where V0 and V2 differ, and why that matters here

V0 and V2 validated **two structurally different mechanisms** — temporal displacement within
one timeline (V0) versus cross-modal divergence between renderings of one source (V2) — not
the same mechanism proven twice. That distinction matters for the decision below: two
independently-mechanistic validations is a meaningfully stronger base for extracting what's
*invariant* (the gimmick test, the per-component provenance need, the independent-access-
routes principle) from what's *prototype-specific* (V0's ordering UI, V2's picker UI) than one
validation repeated would have been.

---

## Definition of a CripMinds publication

Starting from the candidate direction and refining it against the evidence above:

> A CripMinds publication is an evidence-grounded editorial work in which a disability-derived
> perceptual lens reveals something about its subject that the dominant framing misses — and
> whose form, which is the article in the overwhelming majority of cases, is chosen because
> that form is the one that best exposes the hidden mechanism under investigation. A
> non-article form is warranted only when the mechanism itself requires a reader to notice,
> experience, or compare something that prose demonstrably flattens — never because a
> different form is available, novel, or more visually striking.

Why this phrasing, specifically:

- **"Which is the article in the overwhelming majority of cases"** is load-bearing, not
  decorative. Without it, "form is chosen" reads as implying a deliberate departure from
  default happens (or should happen) regularly. It doesn't, and V1's own Class A finding says
  so directly: prose is "the default, lowest-risk, best-understood medium... most of the
  existing catalog." Choosing prose *is* form-selection working correctly, not
  form-selection being skipped.
- **The disability-lens clause is non-optional and prior to form.** A non-article work that
  reveals nothing beyond "captions can be delayed" or "sound and text differ" would fail this
  definition regardless of how well-built its interaction is — the Core Doctrine's
  commissioning question applies before the form question does, not after it.
- **"Demonstrably flattens"** ties directly to the gimmick test both V0 and V2 actually passed
  under testing, not merely under design intent — see Article-First Test, below, which
  formalizes this same question as a standing gate.

---

## Form-selection model

```
SUBJECT
  → HIDDEN MECHANISM
    → WHAT MUST THE READER BECOME ABLE TO NOTICE / EXPERIENCE / COMPARE?
      → WHAT FORM BEST PRODUCES THAT PERCEPTION?
```

Worked against the actual evidence, not hypothetically:

- **V0:** Subject = live captioning / interpreted access. Hidden mechanism = semantic
  correctness does not guarantee temporal participation equivalence. What the reader must
  experience = holding an unexplained reaction in front of them while its cause is still
  arriving, in real, un-narrated order. Form selected = a Trace-family, reader-paced
  step-through — because the mechanism *is* the reader's own temporal position, which only a
  reader-paced, order-preserving interaction can produce; prose can only report the mismatch
  after it has already happened.
- **V2:** Subject = mediation of one real event across channels. Hidden mechanism = mediation
  produces different objects of attention, not lossy copies of a single original. What the
  reader must notice = a felt divergence between renderings, and that whichever one they open
  first quietly starts to feel authoritative. Form selected = a Multimodal Combination /
  comparison structure — because the mechanism specifically requires holding two or more
  renderings side by side; no single medium can demonstrate its own partiality from inside
  itself.

**The standing rule, generalized from both:** form selection is a diagnostic step performed
per subject, not a menu browsed for variety, and the diagnostic question is the same
falsifiable test both prototypes' own self-reviews actually applied to themselves: *if the
candidate form's distinguishing mechanism (ordering, comparison, spatial navigation, whatever
it is) is removed and the same content is restated in plain prose, does the argument survive
intact?* If yes, the form has not earned its complexity — publish an article. If no, proceed.

**No quotas.** "We need a Field this month" is invalid reasoning under this model, on its own
terms — form follows mechanism, and a month with no subject whose mechanism requires a
non-article form is a month with zero non-article publications, correctly.

---

## Material-selection model

```
FORM
  → MATERIAL
    → TOOL
```

Material classes in scope: prose, documentary image, documentary video, real audio, data,
diagram, deterministic code, animation, generated image, generated video, generated sound,
3D/spatial material, or combinations of these.

**"Generate nothing synthetic" is not a fallback position — in every concrete case actually
tested across V0, V1, and V2, it was the *correct* choice, not a compromise.** V0's own
control analysis rejected generated video/audio for its own subject; all three of V1's
designed future works converged on non-generative approaches; V2 was built entirely from a
real recording and disclosed, mechanical signal processing. Generative AI is production
infrastructure, evaluated the same way any tool is, never an editorial goal in itself.

**One distinction this synthesis makes explicit, because V1 and V2's evidence otherwise risks
being read as "no AI" when it is not:** there are two different senses of "AI/generative"
in play, and conflating them misreads the evidence.

1. **AI-assisted production of deterministic material** — an LLM drafting HTML/CSS/JS (how
   V0 and V2 were literally built), or an AI layer turning a prompt into git-diffable,
   human-reviewed Mermaid markup. V1 found this class *consistently justified and already in
   productive use* — the output is inspectable, deterministic, versioned, and makes no
   independent evidentiary claim about the world.
2. **AI generation of the material itself as an evidentiary-seeming artifact** — a generated
   photo, video, or voice presented (even implicitly, by proximity to real documentary
   material) as if it depicts or records something. V1 and V2 both found this class carries
   real, current provenance risk (metadata doesn't survive re-upload) and a technical mismatch
   with CripMinds' working method (frontier tools lack the frame-accurate timing control every
   validated prototype so far has actually depended on).

The practical question for any future work is not "was AI involved," but: **does the output
make an implicit claim that it depicts, records, or transcribes something real — and if so, is
that claim true and disclosed?** Class 1 rarely triggers this question; class 2 almost always
does.

---

## Provenance model

Carried forward: **Document / Reconstruction / Simulation / Generated Interpretation.**

V2 supplied the evidence V1's stress test lacked: **per-artifact labeling is insufficient in
practice, not merely in edge-case theory.** V2's own text log needed two different labels for
two different claims *inside one representation* (measured timing = Document-grade; topic
paraphrase = explicitly flagged unverified). The editorial requirement, stated at the level
this synthesis is scoped to (no schema, no metadata):

> Every publication must be able to state, for each distinguishable component of the work,
> which provenance class it belongs to — and any compound or ambiguous case (a real quote
> given synthetic voice; a documentary photo extended by generative fill; a real recording
> paired with an unverified description of its topic) must label each axis of the claim
> separately rather than forcing one label onto the whole component.

**Media lineage disclosure should be mandatory for any transformation classified as
meaning-consequential, and unnecessary for anything classified as meaning-preserving.**
Cropping, resizing, format conversion, and decoding don't need reader-facing disclosure;
anything that adds content not present in the source, removes context, or recontextualizes
material does. This is a reader-facing editorial practice — visible in the work's own
explanatory text, as both V0 and V2 did — not a backend metadata requirement.

---

## Media lineage (generalized)

For any nontrivial transformation, a publication should be able to state, in plain language,
three things:

1. **What the source was, or its explicit absence** (invented/demonstration content, clearly
   labeled as such — V0's own practice).
2. **Every step that changed the material's evidentiary status** — added content not present
   in the source, removed context, or recontextualized it — distinguished from steps that
   didn't (a crop is not the same disclosure burden as generative fill).
3. **Who or what performed each such step** — a human editorial decision, a deterministic
   mechanical process (V2's `ffmpeg astats` measurement), or a generative model, and which one.

This is design-only, following V1's original instruction: no lineage schema or metadata format
is specified here, only the editorial obligation.

---

## Accessibility / multimodality model

**Reject "primary work + secondary accessible version" as the default conceptual model.**
Define instead: **multiple access routes or representations**, each independently complete and
operable, each explicitly and honestly described in terms of what it preserves and what it
loses, with no built-in hierarchy assigning one route "original" status by default. Where
relevant, the act of translating between modalities can itself become part of a work's content
(V1's addendum framing, actually exercised by V2's own design).

**Do not claim equivalence.** V2's own finding stands as the governing example: sound, text,
and visual renderings of the identical ten seconds are not equivalent, and the work is honest
about that rather than pretending translation is lossless. Accessibility, in this model, means
meaningful access through multiple genuinely usable routes — not manufactured sameness between
them.

**Two standing QA requirements**, generalized directly from the two real defects V2's testing
caught (not hypothetical concerns, actual bugs fixed in a shipped prototype):

1. Any work offering a reader-chosen entry point or order must be tested with a **non-default**
   entry order, not only the expected/designed-for one.
2. **No substantive content may depend on a hardcoded `hidden` (or equivalent) attribute in
   static markup if JavaScript is required to reveal it.** Visibility for JS-dependent content
   must be set by script on load, so the no-JS default is "visible," never "permanently
   unreachable."

---

## Authorship vs. generation

The presence of AI-generated material anywhere in a publication **does not make the system the
author of the lived experience or source evidence it touches.** Drawing the line from the
Material-Selection model above: human editorial judgment remains non-delegable for —

- **Mechanism selection (SEE)** — deciding what hidden mechanism is actually worth revealing.
- **The disability-lens commissioning judgment** — whether a proposed angle genuinely reveals
  something the dominant framing misses, or merely observes that disabled people are affected
  (the Core Doctrine test, which cannot be satisfied by a tool's output alone).
- **The gimmick-test adjudication (PROVE)** — whether removing a form's mechanism removes the
  argument. This is an editorial judgment call, informed by testing, not a metric a model can
  compute.
- **Provenance labeling and disclosure accuracy** — a human must vouch that a Document-labeled
  component really is one.
- **Any claim touching real people's testimony or lived experience** — non-delegable outright,
  continuing V0's own Signed/Visual-Essay rejection (AI-generated signing as a stand-in for
  authored Deaf expression) as the standing precedent for this boundary.

AI tooling's legitimate role is confined to **MAKE** (constructing or accelerating the
production of material a human has already decided is needed) — drafting HTML from a
description, turning a prompt into editable diagram markup, generating a first pass of
deterministic code. It has no legitimate role in **SEE** or in the lens-claim itself.

---

## Article-first test

Formalized as a mandatory first gate, using the same falsifiable question both V0 and V2
actually asked of themselves in their own critical self-review sections (not a new invention):

> **Could a strong article reveal this mechanism just as well?**
>
> Restate the candidate work's content as plain prose, with its distinguishing mechanism
> (ordering, comparison, simultaneity, spatial navigation — whatever the candidate form's
> actual claim to necessity is) removed. If the argument survives intact, publish an article.
> If something genuinely goes missing — not merely something that reads less excitingly, but
> something the reader could no longer come to know — the non-article form has earned its
> complexity.

V0 and V2 both passed this test under real interrogation, not assumption: V0's "What prose
loses" section names the specific felt-sequencing loss precisely; V2's critical self-review
states directly that an article-with-audio-player version "exists, implicitly... and it is
thinner than the comparison." Any future non-article proposal should be required to write
that same paragraph, in its own planning document, before form-selection proceeds.

---

## Conceptual publication object (design only — no schema)

The smallest set of things a future first-class publication object would need to be able to
state, refined against what V0–V2 evidence shows is actually load-bearing (not a CMS field
list):

- **title**
- **subject**
- **hidden_mechanism** — a plain-language statement of what's being revealed; every one of
  V0/V1/V2's works named this explicitly, and it should be nameable before form-selection can
  even begin, per the Form-Selection Model above.
- **disability_lens_claim** — distinct from `hidden_mechanism`: the answer to the Core
  Doctrine's commissioning question, specifically what a disability-derived way of perceiving
  makes knowable about the subject.
- **form** — one of the taxonomy names, or `article`.
- **materials** — the list of material classes actually used (e.g. `["prose", "real-audio",
  "deterministic-visualization"]`), not a single value.
- **provenance_labels** — per-component, per V2's evidence, not one value for the whole work.
- **media_lineage_note** — present only when a meaning-consequential transformation occurred;
  absent is a valid and common state (true of most articles).
- **accessibility_routes** — a list of independently-operable routes and, for each, what it
  preserves and what it loses; no implicit "primary" flag.
- **publication_status** — at minimum `draft` / `experimental-unpublished` (the
  `published: false` / `noindex: true` convention V0 and V2 both already used safely) /
  `published`.
- **canonical_explanatory_text** — every work so far, however novel its form, still ended in a
  prose explanation component; this isn't optional scaffolding, it's a recurring structural
  need.
- **credits/authorship** — which human editor, which persona voice if any, which tools
  assisted construction and how.
- **generated_material_disclosure** — an explicit flag plus description, present *only* if any
  component is Generated Interpretation; defaults to none, since that has been the common and
  usually-correct case so far.

This is a concept checklist for what information a publication object needs to be able to
answer, not a data model, type system, or validation design.

---

## Article / Work relationship

Existing articles stay exactly where they are, in `_posts`, unchanged — there is no reason
found anywhere in V0–V2 to migrate them, and forcing that migration for conceptual tidiness
would violate the project's own "don't force existing structure to change for elegance" norm.

Conceptual shape, held loosely rather than pre-engineered: **Publication** is the umbrella
concept defined above. **Article** is simply the overwhelmingly common realization of it,
using the article form, living in the existing pipeline unchanged. **Work** is the name for a
publication whose chosen form is a non-article taxonomy form, and which needs its own
lightweight home — not because it's architecturally special, but because `_posts` frontmatter
is shaped around linear prose and doesn't have a natural place for `form`, `materials`,
`accessibility_routes`, or `provenance_labels` as V0/V2 exercise them.

What a Work concretely needs, without deciding *how* yet: a stable URL outside `_posts`'
assumptions (both V0 and V2 already prove root-level HTML files work for this); a path to
discoverability once it graduates out of `published: false` experimental status (a listing
entry somewhere a reader would find it, distinguished from an Article card rather than forced
into looking like one); and the same accessibility/provenance disclosure bar as an article,
demonstrated rather than asserted. Whether "Work" ends up as a Jekyll collection, a curated set
of root HTML files, or something else is an engineering decision explicitly deferred to the
Publication Surface V1 prototype below — not decided here.

---

## Cross-form quality test

A publication should succeed on all of the following, regardless of form:

- **Evidence** — claims are grounded; demonstrated by V0's Ofcom/O'Dell citation and V2's
  verifiable, reproducible signal measurements, both stated with what is and isn't confirmed.
- **Mechanism** — the hidden mechanism is genuinely revealed, not merely illustrated;
  demonstrated by both prototypes' passing gimmick tests under real interrogation.
- **Form** — the chosen form materially contributes; the Article-First Test is the operational
  version of this criterion.
- **Provenance** — transformations and any synthetic material are disclosed appropriately, at
  the per-component granularity V2 showed is actually necessary.
- **Access** — meaningful, independently-operable routes exist, honest about non-equivalence
  rather than pretending translation is lossless.
- **Discovery** — where appropriate, the reader discovers the insight rather than being told it
  first; both V0 and V2 structure explanation *after* experience for exactly this reason.
- **Distinctiveness** — disability-derived perception changes understanding of the *subject*
  itself, per the Core Doctrine, not merely documents that disabled people are affected by it.

This is a shared bar, not a production gate — no scoring mechanism or approval workflow is
specified here.

---

## Roadmap implications

**WHY → KNOW → SEE → GENERATE → MAKE → PROVE** has carried the model well, with one
terminology problem worth naming rather than papering over: **every one of the three
documents that used this roadmap (V0's addendum, V1's master model, this synthesis's own
drafting) felt obligated to explicitly state that GENERATE does *not* mean "use generative
AI."** A label that needs the same correction restated in every document that uses it is
working against comprehension, not for it — especially for a future reader who encounters the
roadmap once, without the accumulated context of all three corrections.

**Recommendation only, not applied:** replace **GENERATE** with **MATERIALIZE** —
"what representational material must exist for the insight to become perceptible" is exactly
what the step has always meant, and "materialize" carries none of 2026's strong default
association with generative AI models. If adopted, it should be adopted going forward from
this document, not retroactively rewritten into V0 or V1 — those are historical records of
what was actually reasoned and decided at the time, and rewriting them after the fact would
be exactly the kind of rhetorical smoothing-over of a documented history this project's own
provenance ethics argue against.

---

## Next engineering prototype (if P1)

**Selected candidate: V2, "What the Room Heard," not V0.**

Reasoning: V0's core mechanism is grounded in real cited evidence, but the scene the reader
actually experiences is invented demonstration dialogue — a reasonable and disclosed choice
for a Format Lab prototype testing a mechanism, but a weaker flagship for the *first* real
Work to exist as a genuine publication object, given the Core Doctrine's evidence-grounding
requirement. V2 is built entirely from a real, provenance-clean, unedited source, and its own
documentation states plainly that it functioned as "a genuine stress test of the V1 ontology,
and it holds up" — meaning V2 already demonstrates the provenance/lineage/per-component-
labeling model this synthesis depends on, in practice, not only in design. V2 is also the
structurally more complex case (three representations plus a comparison stage, versus V0's
two channels); if a minimal Publication Surface can successfully carry V2, it very likely
generalizes to simpler cases like V0, while the reverse is not guaranteed.

**Smallest testable step — sketched, not built:** take the existing `what-the-room-heard.html`
exactly as it stands, and describe what minimal change would let it exist as a real,
discoverable CripMinds Work sitting beside articles, without inventing a new collection type,
schema, or generic format registry:

- A stable public URL (already true — no change needed).
- A minimal, hand-written statement of the Conceptual Publication Object's core fields for
  this one work — `hidden_mechanism`, `disability_lens_claim`, `form`, `materials`,
  `accessibility_routes` — as plain text or front matter, not a new schema.
- One listing entry somewhere a reader would actually find it (e.g. the research index),
  visually and structurally distinguished as a Work rather than dressed up as an Article card.
- Flipping `published: false` to a real published state only after the above exist and the
  same accessibility/provenance bar already met in testing is reconfirmed in that new context.

This single-work test is the entire scope of "Publication Surface V1" — explicitly not a
universal multimedia CMS, generic format registry, model-driven format selector, media-
generation pipeline, plugin architecture, or mass migration of existing articles.

**Named limitation of the evidence base, not glossed over:** neither V0 nor V2 tested a work
requiring real, licensed, or otherwise friction-heavy third-party documentary sourcing — V2
explicitly chose its source partly *because* it avoided that friction ("no licensing
complexity around broadcast footage or a specific building"), and V1's Work D ("The
Interpreter's Frame") was passed over as V2's secondary candidate for the same reason. Whether
this publication model holds up under real sourcing friction is a genuinely open question this
synthesis cannot answer and does not claim to.

---

## Decision

**P1 — Publication model justified.**

V0 and V2 validated two structurally different mechanisms, both under real testing rather than
design assertion alone, both passing a falsifiable gimmick test, and both surfacing genuine,
generalizable findings (per-component provenance necessity, the two QA lessons above) rather
than only prototype-specific ones. V1's affordance research and tool landscape, and the
provenance/accessibility models it proposed, were independently stress-tested by V2's actual
build and held up, with a real refinement (per-component labeling) rather than needing to be
discarded. This is enough to define a broader model and proceed to exactly one minimal
Publication Surface prototype — not because of the investment already made in Format Lab, but
because two independently-validated mechanisms are sufficient to separate what's invariant
across them from what's specific to either one, which is precisely what a model requires that
a single prototype cannot supply.

This is not P2: the unresolved question named above (real-sourcing friction) is real, but it
is a question the *next* Work should test, not a gap in the form-selection, provenance, or
accessibility model itself — those held up under the two mechanisms actually tested. This is
not P3: two independently-mechanistic, independently-tested validations, each surfacing real
bugs and real refinements under actual testing rather than only being designed, is more than
"non-article experiments have not demonstrated enough distinct value" can honestly claim.
