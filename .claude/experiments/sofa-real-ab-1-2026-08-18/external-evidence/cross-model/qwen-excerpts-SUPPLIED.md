# Qwen 3.7 Plus — still FULL_RAW_NOT_FOUND

No raw Qwen output or reasoning trace has been recovered or supplied. Excerpts below remain
**PARTIAL_VERBATIM as supplied**, ORIGIN = HISTORICAL SESSION HANDOFF.

## Reasoning excerpts as supplied

1. "no motive, intention, or causal link can be assumed"
2. "the contrast lies in agency: the present viewer drifts at will while the past is trapped in presentation"
3. "the living are offered choices... while the dead artists ... had none."

## Final-output excerpts as supplied

4. "The pleasure of uncovering was made available only by the fact that the maker remained unseen."
5. "posthumous discovery into a house style"
6. "George, Walter, and Hasegawa cannot. They are relying entirely on how they are presented."
7. "dead artists ... had no such choice."

## Independence: downgraded from "plausible" to UNKNOWN

An earlier pass read the divergences from B.3 (word order, "they are" vs "they're", Hasegawa named)
as evidence of a separate generation. That reading is weaker now that Grok and Perplexity are both
confirmed to have been fed B.3's text as their source.

Excerpt 5 is B.3's phrase exactly. Excerpt 4's "the maker remained unseen" is as easily a paraphrase
of the corrupted line in the pasted source — "the maker never gto be seen far outside the city's
confines" — as an independent formulation. Nothing here distinguishes the two.

**Treat Qwen as unknown, not as corroboration.** What would resolve it is not the output but
**the exact text Qwen was given**. See `CONTAMINATION-FINDING.md`.

## Why the reasoning trace still matters if it is ever found

Its diagnostic value was that the model stated the grounding boundary (excerpt 1) and then crossed
it (excerpts 2-3). If Qwen's input was also contaminated, that reads differently — as a model
noticing a boundary and then deferring to a conclusion already present in its source. Only the raw
input can tell those apart.
