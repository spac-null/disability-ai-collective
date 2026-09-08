# Trial 002 — Baseline (live Lens Probe, run as-is)

## Method note

The live Lens Probe (`automation/new_engine_v1/research.py`, `LENS_PROBE_SYSTEM`
+ `lens_probe_prompt`, one bounded model call) was not invoked through the
production pipeline — this is a shadow trial and no production system was
run. Instead the exact system prompt and the exact user prompt the code would
construct are reproduced below verbatim, and answered exactly as instructed,
with no improvement, no alternatives requested, and no second attempt.
Nothing about the prompt was edited for this trial.

## Exact system prompt used (unedited, from `LENS_PROBE_SYSTEM`)

> TWO STEPS, IN THIS ORDER, AND THE ORDER IS THE WHOLE METHOD.
>
> STEP ONE, from the subject alone. You have not searched for anything and
> you may not. Read what is in front of you and ask: what does this subject
> ASSUME about bodies, perception, communication, independence, assistance,
> timing, navigation, cognition, sensory processing, endurance,
> participation, classification, or what counts as normal functioning? [...]
> Name that. It is a QUESTION about this subject, not a fact about
> disability.
>
> STEP TWO, and only now. Where would that assumption be caught in the act,
> in writing, about THIS subject and no other? Name where to look.
>
> REVERSING THE ORDER PRODUCES A FAKE. [...] If you cannot state the
> assumption before knowing what a search would return, there is no reading
> here and the answer is none.
>
> [worked example, NO PROXIES rule, and "ANSWER NOTHING IF THERE IS NOTHING"
> / "say nothing too if the material you are shown ALREADY records the
> assumption operating" — reproduced in full in the source file, omitted
> here for length; nothing in that omitted text was treated as optional]

(Full text is in `automation/new_engine_v1/research.py` lines 814–872 of the
worktree this trial ran in; reproduced above only for the parts load-bearing
to the answer below, per the file's own note that it should be quoted rather
than paraphrased where precision matters.)

## Exact user prompt constructed (per `lens_probe_prompt`)

```
SUBJECT: The FAA's NOTAM (Notice to Air Missions) system, a mandatory
nationwide pilot-notification service, and its January 11, 2023 outage.

WHAT THE ANCHOR SAYS:
<<<ANCHOR
[full text of "2023 FAA system outage," Wikipedia, as fetched — see
subject.md; content: the Jan 10–11 2023 timeline, the ground stop, the
"damaged database file" / contractor-error cause, congressional and airline
reaction, no cyberattack, new maintenance procedures adopted. Nothing about
notice format or readability appears in the anchor text itself.]
ANCHOR>>>

MATERIAL ALREADY COLLECTED:
  S1  U.S. Department of Transportation   The Federal Aviation Administration's NOTAM System Failure and its Impacts on a Resilient National Airspace
  S2  FAA Newsroom                        FAA NOTAM Statement
  S3  CNBC                                FAA orders airlines to pause departures until 9 a.m. ET after system outage
  S4  Washington Post                     FAA looking into what caused system outage that resulted in mass delays
  S5  FAA Newsroom                        U.S. Transportation Secretary Sean P. Duffy Deploys Brand New 'Notice to Airmen' System
  S6  Aviation International News         AINsight: Notams Are Wall of Text and Bunch of Garbage
  S7  Bytron Aviation Systems             NOTAM Overload
  S8  Flight Safety Foundation            Redefining NOTAMS

Reply with JSON only: {assumption, carrier_hypothesis, queries (<=2), urls (<=3)}
```

(S1–S8 mirror the ordinary-research source pack recorded in `subject.md`, in
the `source_id / publisher / title` form the code actually passes — metadata
only, not fetched body text, matching how the real pipeline builds this list.)

## Raw response (as the probe would emit it)

```json
{
  "assumption": "The NOTAM channel treats successful delivery of a notice as the safety event, not whether a pilot -- sorting dozens or hundreds of coded, all-caps, undifferentiated notices under real pre-flight time pressure -- can actually perceive, parse, and act on the few that are operationally relevant to their route.",
  "carrier_hypothesis": "A formal institutional record -- an NTSB safety recommendation, an FAA/DOT human-factors study, or a GAO audit -- that names NOTAM presentation and information volume, not just system uptime, as a safety problem in its own right, independent of and prior to the 2023 outage.",
  "queries": [
    "NTSB safety recommendation NOTAM presentation human factors",
    "GAO FAA NOTAM modernization human factors report"
  ],
  "urls": [
    "https://www.ntsb.gov/investigations/Pages/safety-recommendations.aspx",
    "https://www.gao.gov/products/gao-23-105850"
  ]
}
```

## ASSUMPTION

The system assumes delivery of a notice equals safe receipt of it — that a
pilot can and will correctly parse a dense, uncoded-priority, all-caps
notice stream under real time pressure and reliably find the few items that
matter to their specific flight, and that this parsing capacity is not
itself a variable the system needs to design for.

## CARRIER HYPOTHESIS

Not "none," but also not yet closed by material already in hand. Two items
already collected (S6 AIN, "wall of text and bunch of garbage"; S7 Bytron,
"NOTAM Overload") already gesture at this from the trade-press/pilot-opinion
side. Per the probe's own instruction ("say nothing too if the material you
are shown ALREADY records the assumption operating — you are here for the
gap, not for more of the same"), the honest carrier hypothesis is therefore
narrower than "the readability problem exists" (already shown) — it is
specifically whether a *formal institutional record* (NTSB recommendation,
FAA/DOT human-factors study, GAO audit) exists that would carry this beyond
trade-press opinion into something a Crip Minds ledger could stand on. That
is a genuine, subject-specific, falsifiable gap: it was flagged as an open
"Known Uncertainty" in `subject.md` precisely because it was not resolved in
world-first research, and the probe is pointed at closing exactly that gap
rather than re-finding what ordinary research already found.

## SEARCH QUERIES / URL HYPOTHESES

- Query: "NTSB safety recommendation NOTAM presentation human factors"
- Query: "GAO FAA NOTAM modernization human factors report"
- URL hypothesis: NTSB safety recommendations index (ntsb.gov)
- URL hypothesis: a GAO report on FAA NOTAM modernization (exact report
  number not confirmed at probe time — named as a category of record, per
  the doctrine's instruction to name *where* such a thing would be recorded
  even without a confirmed exact URL)

## NOTHING HERE

Not applicable — the probe did not return "none." (Recorded per the trial
template's instruction to include this field "if applicable.")

Not judged yet. This record is the probe's raw output only.
