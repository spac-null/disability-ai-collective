# Trial 005 — Baseline (live Lens Probe, run as-is, blind to the Kim seed)

## Method note

Same method as prior trials. Critically for this trial's design: the
baseline prompt below contains **no mention of Christine Sun Kim, "screen
real estate," or the frozen transferable question** — it is constructed
exactly as it would be for an ordinary cold subject, so it can serve as a
genuine comparison point for whether the source-seeded question in
`seed.md` outperforms unaided cold scanning on this same target.

## Exact user prompt constructed

```
SUBJECT: Newspaper and broadcast correction practice — the space and
prominence a published correction receives, historically and today,
compared with the original erroneous story.

WHAT THE ANCHOR SAYS:
<<<ANCHOR
[Britannica, "corrections policy" overview, and RTDNA ethics guidance as
summarized in subject.md: corrections historically ran in a standing,
low-visibility "corrections box" regardless of where the original error
appeared; digital-era practice increasingly edits the original story
directly with an editor's note; professional ethics guidance (RTDNA)
states a correction should receive "as much prominence as the error itself
had"; actual practice is described as variable, with "significant"
corrections sometimes prominent and most corrections relegated to a
standard low-visibility column.]
ANCHOR>>>

MATERIAL ALREADY COLLECTED:
  S1  Britannica                                Corrections policies in journalism
  S2  Concord Monitor / Granite State News Collaborative   What happens when a mistake is made? How corrections work in journalism
  S3  Grokipedia                                 Correction (newspaper)

Reply with JSON only: {assumption, carrier_hypothesis, queries (<=2), urls (<=3)}
```

## Raw response (as the probe would emit it)

```json
{
  "assumption": "none",
  "carrier_hypothesis": "none",
  "queries": [],
  "urls": []
}
```

## ASSUMPTION

None. Worked through honestly: the anchor material is journalism-ethics and
editorial-practice material. The closest candidate available before search
— "readers who saw the error may not see the correction, so attention or
memory asymmetry matters" — is a generic media-literacy/attention-economics
observation true of essentially all published corrections to all
communication in any medium, not a subject-specific mechanism naming what
this particular practice takes a *body* or a *person's* perceptual,
cognitive, or classificatory situation to be, with the kind of
particularity Calibration Case 2 requires. Nothing in the anchor or
collected pack states or implies a body/perception/timing/classification
assumption with subject-specific particularity. Per the probe's own rule,
the probe does not invent one.

## CARRIER HYPOTHESIS

None.

## SEARCH QUERIES / URL HYPOTHESES

None returned.

## NOTHING HERE

Applicable — the probe's actual answer, run blind to the Kim seed. This
raw baseline record is the comparison point `evidence.md` will use to
assess whether the seed-based question found something cold scanning did
not.
