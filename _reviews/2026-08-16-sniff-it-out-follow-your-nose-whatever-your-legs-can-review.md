# Article Review: 2026-08-16-sniff-it-out-follow-your-nose-whatever-your-legs-can
Generated: 2026-08-16 09:09
Status: FLAGGED

## Engagement Read (advisory — not a rule check, not gated on)
Would a real reader actually finish this? Never blocks, never affects the
status above — logged as a data point, not enforced. See _engagement_read's
docstring in review.py for why this exists.

VERDICT: Finish. This earns its length — by around the bus schedule paragraph I was fully in, and the wedding anecdote near the end reframes everything that came before it in a way that makes you want to reread the opening.

HOOK: "The festival can be perfectly happy with disabled artists remaining exactly where Sandra George was — unseen, uncollected, found posthumously by a curator with a moving story to tell. Obscurity is not a bug the festival wants to fix. It's the raw material." That's the move. The distinction between discovery and obscurity-as-product is genuinely sharp, and it arrives as a surprise even to the writer, which makes it land harder.

DRAG: The McMurdo/digital detour is the piece's one real risk. It's intellectually honest — the writer explicitly flags they don't have a clean position — but it runs long relative to its payoff, and a reader who came for the festival/access argument might lose the thread for two full paragraphs. Not a fatal problem, but the likeliest place someone skims.

STOP_RISK: 2 — delayed payoff in the McMurdo section only, and the piece earns enough credit by then to survive it.

AUTHOR_PRESENCE: fused — a specific perceptual/interpretive position (measuring thresholds from across streets, calling ahead, reading festival enthusiasm as infrastructure decision) is already doing interpretive work in the first three paragraphs before any identity is named.

QUESTION_TIMING: early_natural — the shift from "does this festival exclude me" to "what kind of discovery is it selling and who is that built for" arrives organically and early, and is sharp enough to carry the whole piece.

## Shadow Checks (observation only, added 2026-08-09 — do not act on before 2026-08-23, and only with real false-positive data)
Deterministic checks for rules the writer prompt states but nothing has ever verified. Never blocks, never affects the status above.
- Bullet points / numbered lists in body: 0 found
- Forbidden academic jargon: 0 found
- Forbidden corporate/journalese clichés: 0 found
- Ending looks truncated: no
- Seam phrases (announcing a callback instead of just making it): 2 found — back to the, which brings me to
- Repetition candidates (G SHADOW V0, added 2026-08-14 — CANDIDATE LIST ONLY, not a verdict, see _check_repetition_shadow's own docstring): 0 found
- Length adherence (E SHADOW V0, added 2026-08-14 — observation only, see _check_length_adherence_shadow's own docstring): IN_RANGE (2236 words, article_type=essay, target=2800, ratio=0.8)
- STOP-risk (J, added 2026-08-14 — observation only, parsed from the engagement read above, see _extract_stop_risk_shadow's own docstring): 2/5 — delayed payoff in the McMurdo section only, and the piece earns enough credit by then to survive it.
- Human-detail provenance (added 2026-08-14 — observation only, deterministic, see human_detail_provenance.py's own module docstring): 0 personal-contact claim(s) found
- Author presence (B, added 2026-08-14 — observation only, parsed from the same engagement read, see _extract_opening_quality_shadow's own docstring): fused — a specific perceptual/interpretive position (measuring thresholds from across streets, calling ahead, reading festival enthusiasm as infrastructure decision) is already doing interpretive work in the first three paragraphs before any identity is named.
- Question timing (C, added 2026-08-14 — observation only, same call): early_natural — the shift from "does this festival exclude me" to "what kind of discovery is it selling and who is that built for" arrives organically and early, and is sharp enough to carry the whole piece.
- Opening-template match (deterministic, added 2026-08-14 — observation only, see opening_template_detector.py's own module docstring): no match against the recent-article window

## Plan-Follow Read (advisory, added 2026-08-09 — Stage B of the anchor-architecture blueprint. NO CALIBRATION DATA YET — real (article, plan) pairs only started accumulating today; treat this verdict as informal until ~20 have built up and been checked against a human. Never blocks, never affects the status above.)
Checks whether _fable_editorial_brief's pre-generation commitments (correction_moment, resisting_example, opening_shape) were actually executed.
CORRECTION: N/A
RESISTING: PARTIAL — "McMurdo photographs a child reaching toward a removed tablet and sees a kid getting lost. I look at the same image and I'm not sure the kid isn't reaching toward the only room they can actually enter." — writer answers the tension rather than leaving it unresolved.
OPENING_SHAPE: MATCH — plain claim.

## Web Fact-Check (quotes, studies, stats, events — live search)
[VERIFIED] EVENT — (unnamed): "Edinburgh's Art Festival occurred in August" — Edinburgh Art Festival is listed as taking place from 14–30 August 2026, so the claim that Edinburgh’s Art Festival occurred in August is accurate[1][14].
[VERIFIED] EVENT — (unnamed): "The Guardian published a review of the Edinburgh Art Festival on the fourteenth " — The Guardian published “Vile statues, writhing liquorice and kids marooned online: Edinburgh art festival review” on 14 August 2026, matching the claim.[1]
[UNVERIFIABLE] STAT — (unnamed): "The narrator's father drove the 4735 bus in Santo André, in the Brazilian state " — The search results show Santo André/ABC Paulista bus and transit sources, but none confirms that the narrator’s father drove bus 4735 for twenty-two years, and one result instead points to a different line number format 
[VERIFIED] EVENT — (unnamed): "Sandra George was a black photographer who died in 2013" — Multiple sources identify Sandra George as a Black photographer and state that she died in 2013, including Glasgow International’s artist page and a 2026 Guardian article[https://glasgowinternational.org/artists/sandra-g

## Readability
Flesch Reading Ease : 62.1  (target ≥ 55 — Bregman baseline)
FK Grade Level      : 8.3  (target ≤ 11)
Avg sentence length : 14.8 words
Word count          : 2300
Verdict             : PASS
Length bucket       : 2300 words (target was 2800 words)

## Rule Compliance
CHECK_FAILED: Response truncated by max_tokens (model=openrouter/claude-sonnet-4.6, finish_reason='length', completion_tokens=1110, reasoning_tokens=None)
[FAIL] RAW — self-referential "argument": "Solnit builds a whole argument that walking is how you think, how you resist, how you belong to a pu"

## Citations
[FLAG] Edinburgh Art Festival takes place in August 2024 | SOURCE: UNATTRIBUTED (reviewer's account only)

[FLAG] Sandra George was a Black photographer who documented Craigmillar, a working-class neighbourhood in Edinburgh | SOURCE: UNATTRIBUTED

[FLAG] Sandra George died in 2013 | SOURCE: UNATTRIBUTED

[FLAG] Sandra George never showed her work in her lifetime | SOURCE: UNATTRIBUTED

[FLAG] Sandra George's photographs were found by a curator after her death | SOURCE: UNATTRIBUTED

[FLAG] Rebecca Solnit's book *Wanderlust: A History of Walking* argues that walking is how you think, resist, and belong to a public | SOURCE: Rebecca Solnit, *Wanderlust: A History of Walking* (attributed but paraphrased)

[FLAG] Eva Rothschild exhibited at the Fruitmarket, described as filling the space with rubber hoses coiled in large loops | SOURCE: UNATTRIBUTED

[FLAG] Jamie Fitzpatrick exhibited clay statues of war criminals with red plasticine smiles at Edinburgh Printmakers | SOURCE: UNATTRIBUTED

[FLAG] Wendy McMurdo has a show at the Scottish National Portrait Gallery of children with technology digitally removed from photographs | SOURCE: UNATTRIBUTED

[FLAG] The Guardian published a review of the Edinburgh Art Festival on 14 August | SOURCE: UNATTRIBUTED (no journalist named, no article title given)

[FLAG] Direct quote attributed to the Guardian review: "You've just got to follow your nose and hope you sniff out something you like." | SOURCE: UNATTRIBUTED (reviewer unnamed)

[FLAG] Direct quote attributed to the Guardian review: "It's impossible to figure out how any of it fits together." | SOURCE: UNATTRIBUTED (reviewer unnamed)

[FLAG] Direct quote attributed to the Guardian review characterising McMurdo's work: children "drifting into online worlds, and at risk of being lost in them for ever." | SOURCE: UNATTRIBUTED (reviewer unnamed)

[FLAG] The festival includes a show on Calton Hill | SOURCE: UNATTRIBUTED

[FLAG] The writer's father drove the 4735 bus route from Santo André to ABC Paulista in the Brazilian state of São Paulo for twenty-two years | SOURCE: Personal testimony, unverifiable

[FLAG] The essay was written during Disability Pride Month 2024 | SOURCE: Author's assertion

---

**Editorial notes warranting particular scrutiny:**

**Sandra George claims** are the most consequential and the least sourced. Three distinct factual assertions — her background,

## Notes
- Article is LIVE — async review only
- Verify flagged items and correct if inaccurate
- Delete this file when reviewed