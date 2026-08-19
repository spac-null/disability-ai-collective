# WG-6B post-repair re-audit — execution notes

## Instrument fidelity

Extraction system prompt: read verbatim from the frozen WG-3A file,
sha256 45586e5f37b881cfb08e8a4bc9d7e9583788079b75c4f6aa0de47be1ef35fe95
(identical to the file WG-5 used).

WG-4A system prompt: read verbatim from the frozen WG-4 file,
sha256 7a4937c9ef8dadf962951e03d8ff97b440112e5e1082d7123ee795f28dc67b3b

WG-4B system prompt: read verbatim from the frozen WG-4 file,
sha256 3e4739d24ea15b4f49102815f2fe8fdaa9b3f249f62721e3e22371fe26c343f8

No system prompt was retyped, edited or tuned for the post-repair pass.

## Call log

Extraction: 3 blind fresh-context calls over the PATCHED articles.
  form1-3  86 propositions (pre-repair 81)
  r2       81 propositions (pre-repair 81)
  r3       72 propositions (pre-repair 74)

Verdict: 6 blind fresh-context calls (WG-4A + WG-4B per article).

## Infrastructure re-run (NOT a content retry)

The first `r2-wg4a` call terminated on an API error ("Connection lost
mid-response") and wrote NO output file — the stage was verified empty before
relaunch. It was re-launched once with the byte-identical frozen prompt.

This is an infrastructure re-run of a call that never completed, not a retry of a
completed call whose content was unsatisfactory. It is recorded here because the
distinction matters: WG-6B's no-retry rule governs the REPAIR stage, and no
repair call was ever re-run. Every repair result in this experiment is a
first-and-only call.

## An earlier read of r2-wg4b saw 82 rows

An intermediate read of `r2-wg4b-raw.json` reported 82 rows while the agent was
still finalising the file; the agent subsequently rewrote it. The committed file
has 81 rows, 81 unique IDs, and aligns exactly with the 81-proposition r2
extraction — zero duplicates, zero IDs absent from the extraction. Verified.
