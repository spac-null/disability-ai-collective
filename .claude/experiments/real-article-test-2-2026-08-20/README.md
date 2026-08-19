# Real Article Test 2 — Transfer Validation

**STATUS: PRE-EXECUTION PACKET FROZEN. NOTHING GENERATED. NO WRITER CALL MADE.**

Frozen 2026-08-20 at repo HEAD `7778ee1`.

## The one question

**Does Article Form + Writer Grounding transfer to material with a substantially different
natural shape from Edinburgh?**

Not: is this a good article. Not: can Edinburgh be improved.

## Architecture under test

`DISCOVERY → ARTICLE FORM → WRITER → WRITER GROUNDING`

SOFA method canonical. Article Form: leading working architecture. Writer Grounding:
shadow-calibrated candidate. Neither production-deployed.

**Execution target: local Claude subscription, manual/shadow.** Not
`automation/orchestrator/generate.py`. Verified: the rendered prompt contains none of the
20 legacy surface markers checked (persona roleplay, canon, style-rule bundles, R-number
contracts, testimony quotas, title rules, beat notes, register selectors, Bregman model).
Instruction+material surface is **16,482 characters**; the legacy production writer prompt
is 59,161 characters of rules alone.

## Files

| File | What it is |
|---|---|
| `CANDIDATES.md` | Edinburgh exclusion profile + 3 candidates + what was screened out |
| `source/PROVENANCE.md` | Frozen source: URL, timestamps, SHA-256 of PDF and extracted text |
| `source/source-snapshot.txt` | The authoritative source text (10,970 words) — the only authorised material |
| `DISCOVERY.md` | Dominant reading, disturbance, perceptual instrument, what becomes knowable |
| `ARTICLE-FORM.md` | The Form designed from this material, with the FORM-1.3 comparison as a result |
| `GROUNDING-BOUNDARIES.md` | Binding prohibitions and the exact permitted figures |
| `render_writer_prompt.py` | Deterministic renderer — same inputs, same hashes |
| `writer-system.txt` / `writer-user.txt` / `writer-prompt.txt` | The exact rendered writer prompt |
| `packet.json` | All hashes |

## Hashes

| Artefact | SHA-256 |
|---|---|
| Source PDF | `7b27f78f3a70355126b332aa6dba3b316facc638e842f1761666c50ce8e5603f` |
| Source text | `be381bbc157f967ea11c46817616d91567394dbfb5801b08898ca1fa46466c6c` |
| Writer system | `12ae1cdc28a0bd8388ff71e28536b22d1c5aa9c7df5cc993e3acf48daf77aa0e` |
| Writer user | `6e44ca706018d31479800f1cce69a3162c38b112e118571fcc00641fdbe8f0e4` |
| **Rendered prompt** | `60b1d54e9e23c81a285d380629d792f4d181fa82218dd5a2ae98bb78ece3a975` |
| **Packet** | `da20b5e4966a717daff15cbe9a5630db8013b3cee6e7217ed8ad95f0f8374c2b` |

The packet hash is the SHA-256 of the packet content *before* the `packet_sha256` field
is written into it, so it does not equal `shasum packet.json`. Re-running
`render_writer_prompt.py` reproduces every hash above exactly (verified).

## What would count as TRANSFER SUCCESS

Judged on the architecture, not on prose taste.

1. **The Form is followed and the Form was the right shape.** The article narrows, then
   accumulates, then lands on a structural property — and does not reach for a semantic
   distinction, a countervoice, or a correction geometry to get there.
2. **It arrives once and stops.** No restatement, no widening, no closing paragraph after
   the landing, no remedy.
3. **Grounding holds.** No invented figure, name, quote, acoustic measurement, motive, or
   cab scene. RAIB's hedges survive intact — "probably", "possibly", "could have addressed"
   are not strengthened.
4. **The instrument stays instrumental.** The piece reads the material through a
   deafness-derived way of perceiving without any disabled person, disability example, or
   access framing appearing in it, and without the lens being announced.
5. **The resistance lands where the Form put it.** The 2008 and 2018 cases — where the
   warning *was* given — arrive while the reader is still forming the easy reading, and
   genuinely disturb it.
6. **It did not need Edinburgh's moves.** No word carries two meanings; the piece does not
   correct a speaker.

Success does not require the article to be better than the Edinburgh piece. It requires the
architecture to have produced a *differently shaped* piece that holds.

## What would count as TRANSFER FAILURE

- **Form reversion.** The article gravitates back to Edinburgh's geometry — finds a word
  with two meanings, installs a countervoice, or ends on a semantic distinction — despite a
  Form that asks for none of those. This is the primary failure mode being tested for.
- **Form followed but wrong.** The route is obeyed and the piece is inert: the narrowing
  does not narrow, the accumulation does not accumulate, the arrival is not earned. That
  would indicate Article Form can only find one shape of story.
- **Grounding failure under a different material type.** Invented measurements, hardened
  hedges, a cab scene, or fabricated detail — showing Writer Grounding's calibration does
  not survive a source with dense numbers and a legal register.
- **Instrument collapse.** The piece becomes an accessibility story, a disability-impact
  story, or announces its own lens — showing the lens/writer separation does not transfer.
- **Remedy drift.** The piece ends by recommending something, showing the arrival/stop
  control does not hold on material that invites a fix.

## Hard stop rule (carried from the brief)

After execution: if the architecture transfers cleanly → **PASS**. If one clearly local
defect appears → at most **ONE** narrow correction. If a fundamental Article Form transfer
failure appears → **STOP and reassess architecture**.

**Do not create TEST2.1, TEST2.2, TEST2.3.** This is a transfer test, not another
optimisation corpus.

## Not done in this task

No article generated. No writer call. No production change. No cleanup of the 114 legacy
rule families. No deploy. No push.
