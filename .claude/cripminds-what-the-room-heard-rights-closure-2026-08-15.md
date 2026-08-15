# What the Room Heard — Source Rights Closure — 2026-08-15

Branch: `publication-surface-production-candidate-2026-08-14`
Follows: `5a9dfc9` (minimal production integration, rights-held)

## Why the prior source was rejected

`assets/format-lab-v2/room-source.ogg` previously pointed at *Old Bell System intercept
recording* (Wikimedia Commons, uploaded by YborCityJohn, 2020-03-19). Its only rights basis
was the uploader's own unsupported assertion — "This file is in the public domain because it
was never copyrighted by the Bell System or AT&T" — with no independent legal citation, no
Commons deletion/undeletion discussion resolving the claim, and no confirmation of the
recording's actual date relative to the copyright-regime boundaries that make "never
copyrighted" theories for network recordings legally nontrivial. Rejected outright, not
argued into acceptability, per instruction.

## Replacement source — rights record

- **Title:** "Sounds of nature recorded on a Zoom H4N in Grunewald near Berlin"
- **Creator:** Freesound user `dbspin`
- **Original source:** https://freesound.org/people/dbspin/sounds/245286/
- **Mirror used for this Work:** https://commons.wikimedia.org/wiki/File:245286_dbspin_grunewald.wav
  (mirrored to Commons 2014-10-18 by Commons user Nicor; mirroring does not affect the
  license, since the CC0 dedication was made by dbspin, the creator, on Freesound directly)
- **License:** CC0 1.0 Universal Public Domain Dedication — an explicit waiver of all
  copyright by the creator, not an inferred or asserted-by-a-third-party PD status
- **Own work:** yes — the Commons file description states the recordist's own equipment
  ("Zoom H4N") and location; this is a self-recorded field recording, not a re-digitized
  historical artifact of disputed authorship
- **Permitted reuse:** commercial reuse permitted, modification permitted, no attribution
  legally required (attribution given anyway, as a matter of editorial practice)
- **Content check:** no third-party music, no identifiable individuals, no spoken testimony,
  no consent issue — ambient woodland recording only (wind, indistinct rustling, an
  unidentified acoustic event)
- **Transformation performed by CripMinds:** trimmed to a 12.0-second excerpt (seconds
  12.0–24.0 of the ~4:20 original); decoded to mono for analysis; re-encoded to Ogg/Opus for
  web delivery. No other editing. CC0 permits this without restriction.

This is a substantially clearer rights basis than the prior source: the dedication is an
explicit act by the identified creator, not an inference about a decades-old corporate
recording's copyright history.

## What changed downstream of the source swap

Every source-derived representation was regenerated from the actual replacement audio, not
carried over from the Bell System data:

- RMS loudness re-measured in 100ms windows via `ffmpeg astats` (same method/tool as before)
  → 120 real data points (12.0s clip), not 104 (10.3s clip) — the count follows the new
  clip's actual duration, not preserved from the old source.
- Region segmentation re-derived from scratch: 3 honest regions (Ambience / Event /
  Ambience) rather than the old 5 (Tone/Speech/Pause/Speech/Fade), because that's what the
  real data actually shows. Forcing 5 regions onto this recording would have meant inventing
  boundaries that aren't there.
- The region-detection rule itself was adapted (rolling-average threshold + gap-bridging),
  disclosed on the page, because natural wind-driven sound doesn't have the clean on/off
  boundaries a studio/network tone does — stated as an explicit, honest difference from the
  prior source's methodology, not hidden.
- Textual event log re-authored: the cause of the mid-clip loudness rise (wind gust vs.
  animal/bird call) is stated as unconfirmed, matching the same evidentiary honesty as the
  original's "words not independently verified" disclosure, applied to what this new source
  actually requires flagging.
- Removed a claim that is no longer true: the old source faded to near-total measured
  silence (−101dB) at its tail; this outdoor field recording never approaches silence at any
  point. The page now says so explicitly rather than reusing "fade to silence" language.

## Reader-facing status cleanup

`publication_status` changed from `"published — Format Lab Work, promoted from prototype
v2"` to `"published"`. The Format Lab lineage remains available in this internal document and
the earlier `.claude/cripminds-publication-surface-v1-2026-08-14.md`, not in reader-facing
copy.
