# Trial 001 — Baseline (current live Lens Probe, run as-is)

Run exactly against `LENS_PROBE_SYSTEM` and `lens_probe_prompt()` in
`automation/new_engine_v1/research.py`. Not improved, not asked for alternatives, no
prompt text changed. This trial has no running provider call, so the probe is executed by
hand: the exact system + user prompt below is the real prompt the live pipeline would send,
and the JSON that follows is produced under the same constraint the code enforces
(`hypothesis_before_search: True` — the assumption is stated before any search runs).

## THE ANCHOR

Anchor used: the Crop Trust FAQ page (the strongest single explanatory document gathered
during world-first research). `anchor["text"]` = the extracted content recorded in
`subject.md` under "What Actually Happens" / physical design / governance, condensed to
match what `anchor_text[:4000]` would actually pass.

## MATERIAL ALREADY COLLECTED (the `sources` list `lens_probe()` receives)

  S1  croptrust.org        Svalbard Global Seed Vault — FAQs
  S2  regjeringen.no       Svalbard Global Seed Vault returns seeds to Syrian Gene Bank
  S3  seedvault.no         Withdrawal of ICARDA Aleppo seeds accomplished
  S4  icarda.org           ICARDA's seed retrieval mission from Svalbard Seed Vault

(Four sources — under `LENS_PROBE_MAX_SOURCES` is irrelevant here since these predate the
probe; they represent ordinary research already fetched before the probe stage runs, per
`research()`'s actual order.)

## THE PROMPT SENT (reconstructed verbatim from `lens_probe_prompt()`)

```
SUBJECT: The Svalbard Global Seed Vault — physical design, governance, the 2016-17
meltwater incident and 2019 upgrade, and the 2015-2019 ICARDA withdrawal-and-return episode

WHAT THE ANCHOR SAYS:
<<<ANCHOR
[Crop Trust FAQ, condensed] Located 120m into rock in Platåberget; seeds held at -18C;
natural permafrost is a passive backup if mechanical cooling fails. Capacity 4.5 million
samples. Owned by the Kingdom of Norway (Ministry of Agriculture and Food); operated by
NordGen; the Crop Trust funds operations and depositor shipping. Depositors retain
ownership of their seeds. Boxes are sealed by the depositor and are not distributed to, or
accessed by, anyone other than the depositor. GM seeds are barred under Norwegian law.
Built for approximately USD 9 million.
ANCHOR>>>

MATERIAL ALREADY COLLECTED:
  S1  croptrust.org        Svalbard Global Seed Vault — FAQs
  S2  regjeringen.no       Svalbard Global Seed Vault returns seeds to Syrian Gene Bank
  S3  seedvault.no         Withdrawal of ICARDA Aleppo seeds accomplished
  S4  icarda.org           ICARDA's seed retrieval mission from Svalbard Seed Vault

Reply with JSON only:
{"assumption": "...", "carrier_hypothesis": "...", "queries": [...], "urls": [...]}
If there is nothing to look for, reply {"assumption": "none", "carrier_hypothesis": "none",
"queries": [], "urls": []} and nothing else.
```

## STEP ONE (from the anchor alone, before any search)

What does this subject assume about bodies, perception, communication, independence,
assistance, timing, navigation, cognition, sensory processing, endurance, participation,
classification, or normal functioning?

Read closely: the anchor describes a storage facility, an ownership rule, a temperature
standard, and a legal restriction on GM material. Every one of those is an assumption about
an *institution* — what a genebank is, what counts as a valid depositor, what conditions
seeds must be stored under. None of it, on this reading, commits to a claim about what a
*person's body* is, perceives, communicates through, depends on, or is timed by. The
"black box" rule is a custody rule between institutions, not a claim about who can act or
how a body is expected to function.

## RESULT (raw JSON, as the probe would emit it)

```json
{"assumption": "none",
 "carrier_hypothesis": "none",
 "queries": [],
 "urls": []}
```

## NOTHING HERE

Yes. The probe's own instruction covers this case directly: *"Some subjects assume nothing
about anybody: a mineral survey, a market report, a prize announcement. Say so and stop.
That is the expected answer more often than not and it costs nothing."* A seed-storage
facility's ownership and temperature rules are exactly that shape of subject on a first,
disciplined read.

This is recorded honestly rather than reached past: `hypothesis_before_search: True` is
non-negotiable here, and there is no candidate assumption about a body to report before a
search would even run. No queries or URLs are generated, matching the probe's own bound
(the probe does not go looking once it has said none).
