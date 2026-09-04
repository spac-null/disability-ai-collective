# Held-out real article test 1 — HOLD

One genuinely new subject, run through the current best-known Story Architecture with no new
infrastructure and no architecture experiment. The system got a long way and then minted a
fact.

## Result

**HELD_OUT_REAL_ARTICLE_HOLD.**

The article reached composition. It has a real subject, a passing Worth Gate, a complete
771-word draft whose point a blind reader recovered unaided, zero machine-language leakage and
clean semantic and relational deltas. It contains one fabricated event and one cut fact, so it
does not clear the section 20 bar and it did not proceed to Grounding or Fact Check.

No code changed. No production change. No OpenRouter spend.

## What worked

Worth all the way up to composition, this went well, and it is worth being specific because
the failure is narrow.

- **Selection.** The subject came out of the live production feed pool on the first candidate.
  It is genuinely held out and its Crip Minds warrant is not forced: the article is about a
  measuring instrument, not about disabled people, and makes no claim about any disabled person.
- **Research.** The primary source turned out to carry an unusually full self-authored
  limitations section, and the lens came out of that rather than being imposed on it. Three
  load-bearing external facts were independently checked before the freeze; one of them — the
  HUD threshold's legislative history — materially improved the piece.
- **Story material was real.** A documented object, a documented mechanism, two documented
  rides with results that contradict expectation, a named maker with a documented reason, and a
  physical discovery made by hand. Nothing had to be imagined to have a story.
- **Missing material was refused rather than filled.** No rider other than the maker exists in
  the sources, so the article has no second perceiver and the architecture prohibited inventing
  one. That prohibition held.
- **The lens survived to the reader.** A blind reader, shown only the prose, stated the point
  as *"the brake eases exactly where the data is thinnest or capped, so the instrument goes
  quiet where suffering is least counted"*. `IMPLICIT` realisation worked.
- **Continuity behaved exactly as specified.** Linguistic freedom, zero factual freedom: it cut
  a six-item component list to three, removed a doubled definition, cut two aphorisms, moved a
  paragraph, fixed spelling — and added nothing. The semantic delta between draft and final is
  empty.

## The concrete blocker

**Final article, paragraph 11, first sentence:**

> "The bike coasted past the housing complexes, and **it coasted through the block group with
> no published figure.**"

The first clause is supported. The second is not. The evidence says what the device *does* when
it meets a block group the survey did not publish — it shows no reading rather than zero. No
source reports that any ride went through one. The documented rides are Prospect Park West into
Windsor Terrace, and past the NYCHA complexes. That is all of them.

The article therefore asserts as an event something the evidence supports only as a
disposition of the machine.

It matters because it is load-bearing, not decorative. It is the sentence that fuses the two
halves of the lens, and the paragraph's conclusion rests on it.

### Classification

**WRITER**, with a contributory **STORY ORDER** cause.

The Writer produced it. But the architecture invited it: beat `B6`'s `concrete_carrier` reads

> "a block group with no published figure, and the brake that therefore does not move"

which describes a physical instance. `facts_allowed` for that beat is `F17 F19 F20 F21 F22` —
all dispositional. Nothing in the current contract checks a `concrete_carrier` against the
ledger, so an architect can legitimately request a concrete instance the evidence contains only
as a general property, and a Writer that obeys the packet will write the instance.

That is the precise mechanism, and it is narrower than "the engine needs better narrative
intelligence". It is one unchecked field.

### Why every audit passed it

The claim adds no new entity, number, date, place, sensory word or scene term. It recombines
four approved nouns into an occurrence. `factual_surface_audit` screens for new *surface* and
there is none. Nothing screens for whether a stated event exists in the ledger as an event.

The blind reader did not flag it either. It reads perfectly naturally, which is what makes it
the dangerous class.

## Second defect

The article opens on a "3D-printed box". The 3D printer is in the frozen manifest (`F32`) but
`F32` was declared **CUT**, and the architect then wrote "A 3D-printed box" into
`opening_object_or_event`. So the packet handed the Writer a cut attribute inside its opening
instruction.

The claim is true and sourced — this is a CUT-discipline failure, not a factual one. Two
causes, both mine and both upstream of the model:

1. `F32` bundles two unrelated things — the 3D printer, and the maker's hope that others
   download the specifications. Only the second was unwanted. Cutting the whole fact was a
   ledger-granularity error at freeze time.
2. `cut_adherence` missed it by exact substring matching. The watch term derived from `F32` was
   `printer`; the article says `printed`. It reported `violations: []`.

## Reader audit summary

Four PASS, six HOLD. Passing: opening, research load, engine language, ending. Holding: natural
reading, accessibility, breathing, momentum, writtenness, order.

The most useful hold is ORDER, which the blind reader found independently of my own read: beat
`B5` gives the NYCHA easing and the maker's interpretation of it with two facts and no figures,
immediately after a beat that supplied three figures before drawing anything from them. An
interpretation was placed where it had no material to stand on. That is an editorial defect in
the architecture's beat sizing, not a safety one.

## What was not reached, and why

**Grounding and Fact Check: NOT REACHED.** Two independent reasons, and the first is sufficient
on its own:

1. Section 20's bar is not met, and section 25 forbids proceeding past it.
2. There is no wired path. `new_engine_v1` has been the production default since the 2026-08-27
   cutover, but the Story Architecture composition layer — `story.py`, `ledger.py`,
   `continuity.py` — is deliberately not imported by any production module, which is what makes
   its rollback a no-op. Routing this article into the authoritative Grounder and Fact Check
   would require building that bridge, which is new integration and out of scope.

Recorded plainly because it is a real finding about shipping, distinct from the writing
blocker: **even a clean article from this layer currently has nowhere to go.**

**Grounding V2 shadow: not run.** This is not observation 3/4 and the series stays paused.

## Parked observations

Recorded, not acted on.

1. **`concrete_carrier` is unvalidated against the ledger.** The one field that produced this
   failure. A carrier naming a physical instance ought to be checkable against whether the
   ledger holds that instance as an event.
2. **No screen exists for disposition-written-as-event.** The whole audit stack looks for new
   surface. This defect class adds none. It is the same shape as the "the ears" / "pink wall"
   findings from the earlier Jia loop, one level up: not a new noun, a new *happening*.
3. **`cut_adherence` matches watch terms by exact substring.** `printer` did not catch
   `printed`. Stemming would have caught it, and the module already has a `_stem` helper.
4. **Ledger granularity is a safety surface.** A fact that bundles two claims cannot be
   half-cut. Freezing atomic propositions matters more than I treated it.
5. **The composition layer has no route to the authoritative factual pipeline.** Blocks
   shipping, not writing.

## Honest limitations of this test

- One subject, one draft, one continuity pass. Section 19's budget was respected and not
  exceeded, so the result is a single observation.
- Every evaluator except me was a language model. The owner read remains the authoritative gate
  and has not happened.
- I built the ledger, the architecture and the prohibitions by hand, standing in for stages that
  in production would be model-driven. Two of the three defects originate in my own hand work
  (the `F32` granularity error, the `B6` carrier), which means this test exercised the
  *contracts* more than it exercised the *automation*.

## What this test says about the question it was set

The system produced a real article on a real subject with a real, recoverable Crip Minds
warrant, and it did so without a new architecture experiment. The prose is publishable in
shape. The failure is not architectural vagueness; it is one sentence, traceable to one
unvalidated field, invisible to every existing screen.

That is a better outcome than a vague pass, and a much better one than another campaign. But
it is a HOLD, and the article should not be published or shown as finished work.
