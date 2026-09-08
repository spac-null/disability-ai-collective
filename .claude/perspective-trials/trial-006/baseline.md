# Trial 006 — Baseline (live Lens Probe, run as-is, blind to Kim/seed/collision)

## Method note

Constructed with no mention of Christine Sun Kim, the seed question, the
disciplinary table, or the collision question — exactly as it would be for
an ordinary cold subject.

## Exact user prompt constructed

```
SUBJECT: Earthquake magnitude reporting — the USGS's practice of issuing
an automated preliminary magnitude within minutes of an earthquake,
followed by a human-reviewed final magnitude hours to weeks later.

WHAT THE ANCHOR SAYS:
<<<ANCHOR
[USGS FAQ material as gathered in subject.md/methods research: the first
automatic location/magnitude is available about three minutes after an
event; magnitude is updated in the hours and days following as more
seismic-station data arrives (some waves take over an hour to reach
distant stations; some networks deliver data with delay) and as more
time-intensive processing/human review is completed; a second update
occurs days to weeks later when the event is reanalyzed for the archival
catalog. USGS errata material states reports "labeled as automatic...
not labeled as having been reviewed by a seismologist" should be "viewed
cautiously," and documents past cases of "serious errors" reaching
"response organizations and the public."]
ANCHOR>>>

MATERIAL ALREADY COLLECTED:
  S1  USGS                 Why/when does USGS update the magnitude of an earthquake?
  S2  USGS                 Errata for Latest Earthquakes
  S3  USGS                 Why do USGS earthquake magnitudes differ from other agencies?

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

None. This is geophysical-measurement and wave-propagation-physics
material. The closest candidate before search — "the public may not
understand a label distinguishing automatic from reviewed data" — is a
generic information-literacy observation true of nearly any technical
measurement system with a preliminary/final distinction (weather
forecasts, medical test results, financial estimates), not something the
anchor states with subject-specific particularity about bodies,
perception, timing, dependence, navigation, cognition, or classification.
Per the probe's own rule, it is not stated.

## CARRIER HYPOTHESIS

None.

## SEARCH QUERIES / URL HYPOTHESES

None returned.

## NOTHING HERE

Applicable — the probe's actual answer, run blind to everything in
`seed.md`, `methods.md`, and `collision.md`. This is the comparison point
for whether the collision-derived question found something cold scanning
did not.
