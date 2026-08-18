# Finding: the cross-model runs were fed Opus B.3's text as their source

Established 2026-08-19 from raw material supplied by the owner in the preservation session,
compared against artifacts already preserved in this evidence root. **No model was called.**

This finding supersedes the "independence in question" language in
`CROSS-MODEL-CONVERGENCE-FINDING.md`. The question is now answered.

## What was actually pasted to the models

The blind-writer prompt (`raw/blind-writer-prompt-as-supplied.md`) ends with a placeholder:

```
FULL SOURCE

[PASTE THE SAME FULL EDINBURGH SOURCE TEXT HERE]
```

What got pasted in its place is preserved verbatim at `raw/source-text-as-supplied-to-models.txt`.
It is **not** the Guardian review. It is a damaged terminal/screen capture — mangled line wrapping,
words truncated mid-token (`never gto be seen`, `advocver could`, `Sandal's language of discovery`)
— in which **Opus B.3's generated article has been interleaved with the Guardian text**.

## The test

Each phrase below is B.3's own writing, not the reviewer's. Counts are exact-string matches:

| Phrase | Real Guardian source | Opus B.3 | Text pasted to the models |
|---|---|---|---|
| "does something to the festival's cheerful verbs" | 0 | 1 | 1 |
| "The pleasure of uncovering was only made…" | 0 | 1 | 1 |
| "posthumous discovery into a house style" | 0 | 1 | 1 |
| "a rhythm you learn to anticipate" | 0 | 1 | 1 |
| "They are relying entirely on how they're presented" | 0 | 1 | 1 (line-broken) |
| "had no such choice" | 0 | 1 | 1 |
| "breezy verbs never quite reckon" | 0 | 1 | 1 |
| "never got to present herself" | 0 | 1 | 1 |
| "the source never tells us why" | 0 | 1 | 1 |
| "The reviewer's own shrug is telling" | 0 | 1 | 1 |

Ten for ten. Every phrase absent from the real source, present in B.3, present in what the models
were given as "the source."

## Two tells that settle direction of copying

**1. Grok repairs the damage.** The pasted text carries B.3's sentence with characters dropped:

> "The pleasure of uncovering was only made     available by the fact that the maker never gto be seen far outside the city's confines"

Grok's output reads:

> "The pleasure of uncovering was only made available by the fact that the maker never got to be seen."

A model reconstructing a corrupted input produces exactly this. A model independently arriving at
the same thesis does not reproduce a mangled sentence and silently fix its typo.

**2. Perplexity starts from the paste's last line.** The pasted text's final sentence is B.3's
closing line. Perplexity's first article opens with that sentence verbatim, then says: *"That single
sentence — evocative, chilly — is a good place to begin."* It was not converging on B.3's
conclusion; it was handed B.3's conclusion and asked to expand it.

## Consequence for the architecture record

The Article Form reset was justified in
`../source-session-briefs/brief-2026-08-18T21-12-45-line1249.txt` as:

> Opus B.3 - Grok - Qwen independently converged … The remaining failure is NOT primarily
> writer-model choice. The blind-writer interface itself creates a semantic attractor.

On this evidence, Grok and Perplexity converged with B.3 because **B.3's sentences were in their
input**. That is not a semantic attractor in the blind-writer interface. It is contamination of the
source slot. The cross-model leg of that argument does not hold.

## What survives intact

- **B.3 and B.4 remain valid.** Both ran on Opus through the real pipeline against the real
  8,629-character Guardian snapshot (`../../case/source-snapshot.txt`, SHA-256 `fee0a03b…`), both
  are preserved in full with packets and grounding audits, and both reached the dead-artist-agency
  thesis. That is still two clean observations of the blind-writer interface producing it.
- **The Perplexity "for CripMinds" collapse remains a real observation** and does not depend on
  independence: told to write for CripMinds, it moved to ableist curation, captions, audio
  description, plain language, neurodivergent engagement — disability-as-subject, exactly the
  failure the Sofa method exists to prevent. That is worth keeping.
- **The Article Form direction is not refuted.** It is simply less supported than recorded: one
  model twice, rather than three models once each.

## Qwen: still unresolved

No raw Qwen output or reasoning trace has been supplied or recovered. Its excerpts diverge from
B.3 in wording, which previously read as evidence of independence. That reading is now weaker: the
contaminated paste contains "the maker never gto be seen far outside the city's confines", and
Qwen's "the maker remained unseen" is as easily a paraphrase of that damaged line as an independent
formulation. **Qwen's status should be treated as unknown, not as corroboration**, until its raw
output and — critically — the exact text it was given are recovered.

## What would still be worth having

The input each model actually received, per run. The outputs alone cannot establish independence;
this whole finding turned on recovering the input, not the output.
