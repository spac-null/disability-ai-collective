> **SUPERSEDED 2026-08-19 — see `CONTAMINATION-FINDING.md`.**
> This file was written before the raw Grok and Perplexity sessions were supplied. Its central
> question — whether the Grok excerpts matching B.3 meant mis-attribution or contamination — is
> now answered: **contamination**, at the source slot of the prompt. Its closing suggestion that a
> raw Grok artifact would settle the matter was right, and it did. The text below is left
> unedited as the record of the intermediate state.

# Finding: the cross-model convergence evidence is weaker than recorded

Produced during preservation, 2026-08-19. Read-only analysis of already-preserved artifacts plus
the supplied excerpts. **No model was called. Nothing was reconstructed.**

## What the architecture decision rests on

The operator brief that reset the architecture toward the Article Form layer
(`../source-session-briefs/brief-2026-08-18T21-12-45-line1249.txt`) states:

> Using substantially the same blind-writer Edinburgh interface:
> - Opus B.3
> - Grok
> - Qwen
> independently converged on essentially the same new thesis: living visitor has
> freedom/choice to wander vs. posthumously discovered dead artists lack agency/choice
> and independently produced closely related unsupported claims.
>
> Therefore: The remaining failure is NOT primarily writer-model choice.
> The blind-writer interface itself creates a semantic attractor.

Three independent models converging is what licenses "the interface, not the model."

## What the surviving evidence supports

| Source | Raw output | Independence |
|---|---|---|
| Opus B.3 | **Preserved in full** (`iterations/B3/sofa-b3.md`) + packet + grounding audit | n/a — this is the reference run |
| Grok | Not found anywhere | **In question** — all four supplied excerpts are verbatim B.3 |
| Qwen | Not found anywhere | **Plausible** — excerpts diverge from B.3 in word order, contraction, and named artists |
| Perplexity | Not found anywhere | **Contaminated** — opening clause is verbatim B.3 |

So of three claimed independent confirmations, one is confirmed contaminated, one has evidence
that is textually indistinguishable from the reference run, and one holds up on internal evidence
alone without its raw artifact.

## What this does not overturn

The B.3/B.4 rejection does not depend on cross-model convergence. B.3 and B.4 were **both** run on
Opus, both preserved in full with their grounding audits, and both independently reached the
dead-artist-agency thesis. That is a real, twice-observed, fully-evidenced result about the
blind-writer interface. The Article Form direction is not undermined by this finding.

What is weakened is specifically the strength of the claim "three models, therefore the interface."
On surviving evidence that is better stated as: one model twice, plus one plausible second model
without a raw artifact, plus one contaminated run.

## What would settle it

A raw Grok artifact — a saved response, a screenshot, an export. If one exists outside this
machine, it is the single highest-value missing item in the Edinburgh record. If none exists, the
convergence claim should be restated at the strength the evidence actually carries.

**Not** a re-run. Re-running Grok now, after B.3 exists and has been discussed, cannot reproduce
the conditions of a first clean generation.
