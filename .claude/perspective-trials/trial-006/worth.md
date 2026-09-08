# Trial 006 — Worth Gate

Run against `WORTH_SYSTEM` (`automation/new_engine_v1/composition.py`,
lines 677–797) exactly as written, applied to `ledger.md`. Not softened
toward PASS, not told this is "the first Perspective success" — the
ledger is judged on its own facts.

## worth_gate

**verdict: STRONG_INTERPRETIVE_LENS**

**lens_claim:** PAGER turns a life-or-death question — how bad is this
earthquake — into a number, and its own designers chose to publish and
act on that number while it is still admittedly wrong, because waiting
for it to become right costs more than being wrong briefly does; the
system's real history contains at least one case where that choice
produced an overestimate, and the field's own response to it was not to
abandon the choice but to narrow it.

**changes_meaning_how:** A reader's default assumption about "the number"
in a disaster alert is that more accuracy is simply better, and that
publishing something knowingly imprecise is a failure of the instrument.
PAGER's own account inverts this: precision is not free, and the
system explicitly treats the *delay required to get a more accurate
number* as its own form of harm, formally comparable to the harm of the
number being wrong. Read this way, the color-coded alert with its
built-in probability histogram is not a hedge against an imperfect
system — it is the system telling the truth about what kind of claim it
is making, at the moment it is making it. The Van case shows what happens
when that honesty is not enough to prevent the wrong action being taken
anyway.

**evidence_ids:** F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F13, F14

**lens_particulars:** F05, F06, F07, F08 — the specific, subject-specific
design decision (the 20-minute embargo, "the comfort level of the
seismic expert on call," reasoned explicitly against the risk of a
"premature, erroneous alert") and the specific, named, dated real event
(Van, Turkey, 2011) it exists in tension with. Not particulars, correctly
excluded from this list: F01–F04 (general PAGER design statements, true
of the whole system, closer to background/definition than a subject-
specific tension) and F09 (a general stated lesson, not a claim about a
specific event).

**lens_carrier:** PAGER's own 20-minute embargo for its rarest, most
severe alerts, reasoned explicitly as a trade against the real cost of
delay — set against the real, named case (Van, Turkey, 2011) where the
system's ordinary fast-first choice produced a wrong initial reading.

**can_carry_article:** YES. The speed/certainty tension is not a fact
mentioned once and dropped — it structures the whole system's design
(F01–F04), has a real historical test (F08, F10), and a real, bounded
institutional answer (F05–F07) that a reader can sit inside for the
length of a full piece, not just an opening anecdote.

## Reasoning against the gate's own named failure modes, checked
deliberately before finalizing

- **Not WEAK_ANALOGY.** Nothing here rests on resemblance or metaphor —
  every claim is sourced to PAGER's own stated design language or its own
  team's account of a real event.
- **Not the WildSumaco failure (a record about a neighbouring entity).**
  F05–F09 are PAGER's own account of PAGER, and F08 is PAGER's own account
  of an event that happened to PAGER's own alerting — not a record about
  some broader or adjacent system standing in for this one.
- **Not GREAT_GENERAL_STORY_WRONG_PUBLICATION**, though it was seriously
  considered: is "speed vs. accuracy in disaster alerting" simply a good
  general science story with no distinctive way-of-knowing contribution?
  The deciding factor is the gate's own stated bar — an interpretive
  reading does not require disability content, it requires asking what a
  system "has a field for, what it turns into a number, what it drops."
  PAGER's own explicit, structural answer to that question (a probability
  histogram instead of a bare number; a stated position that delay itself
  is a harm) is exactly the shape the gate names as its central mode, not
  an edge case reached for.
- **Not an accessibility fact standing in for the reading** (Case 4)
  — there is no accessibility fact anywhere in this ledger. The
  reading rests on the system's own registration/uncertainty design, per
  the gate's explicit statement that this is a distinct, sufficient basis
  on its own.

## story_candidate

**story_id:** pager-red-alert-van

**carrier_type:** event

**opening_possibility:** The moment, 27 minutes after the ground stopped
moving in Van, Turkey on October 23, 2011, that a number appeared on
screens around the world calling it a red alert — before anyone knew
for certain how bad it actually was.

**real_event_or_change:** PAGER issues a red alert (fatalities and
economic losses) 27 minutes after the M7.2 Van earthquake; a day later,
revised inputs bring the alert down to orange/red, consistent with the
eventual, real losses.

**tension:** The system was built, on purpose, to publish and act on a
number its own designers know might be wrong — because the alternative,
waiting to be sure, costs lives on its own. Most of the time the fast
number holds. Sometimes, like in Van, it doesn't, and the system has no
clean way to take back an alert that already went out.

**reader_first_sees:** A red alert going out to responders and aid
agencies within half an hour of an earthquake most of them have never
heard of yet.

**reader_later_discovers:** The number that went out was already, quietly,
admitted to be uncertain by the system that produced it — and that the
system's own engineers built a narrow, 20-minute pause for the rarest,
worst alerts specifically because they know how much can still change in
that window, but chose not to extend that pause to every alert, because
delay has its own body count.

**causal_chain:**
- {"kind": "SUPPORTED_CAUSAL", "link": "PAGER's stated design position that delay increases loss leads it to publish alerts before source parameters are fully stable", "evidence_ids": ["F02", "F01"]}
- {"kind": "SUPPORTED_CAUSAL", "link": "That design choice is why PAGER's initial Van alert (27 min) could be wrong and only self-correct a day later", "evidence_ids": ["F02", "F08"]}
- {"kind": "CHRONOLOGICAL_ADJACENCY", "link": "PAGER's 20-minute embargo for orange/red alerts and the Van overestimate are both real facts about the same system; the source does not state the embargo was created because of Van, and this piece must not claim that link", "evidence_ids": ["F05", "F08"]}

**evidence_ids:** F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F13, F14

## WORTH: PASS
