# Held-out article → authoritative factual pipeline

One-off adaptor, `automation/heldout_factual_bridge.py`. No cron, no production default,
no schema, no merge, and no change to either component it calls.

## 1. The residual, removed

The one acknowledged unsupported particular is gone:

- was: "Clamped to the front fork of a docked Citi Bike is a 3D-printed box, **with a wire
  running down from it to the brake arm**."
- now: "Clamped to the front fork of a docked Citi Bike is a 3D-printed box."

Removal only. No replacement fact. `F01` supports the attachment to the front fork and the
override of the front brake; `F02` supports the 3D-printed enclosure. The routing detail had
come from the architecture's `opening_object_or_event`, which is left untouched as
instructed — so the field still carries it and the prose no longer does.

Deltas against `WRITER_DRAFT.v3.md`: NEW FACTS 0 · NEW OCCURRENCES 0 · NEW RELATIONS 0 ·
CUT 0 (10/10 watched) · UNSUPPORTED NEGATIVES 0 · MACHINE LANGUAGE 0. Added surface empty,
added relation classes empty, new content words empty. 688 words.

## 2. The bridge

Grounder V1 validates a planner BRIEF's evidence fields against an evidence packet; the
Story Architecture layer has a frozen ledger whose facts already carry a `support_span` and
their source ids. Those are the same object under two names, so each USED fact is presented
as one evidence field whose `source_excerpt` is its frozen span, and the real V1 check runs
unmodified: the span must appear **verbatim** in the source text fetched from the frozen URL.

Two adaptations, both stated because both could hide something if left implicit:

1. **Elided spans are split.** The frozen ledger marks elision with `...`, which can never
   be a verbatim substring. Each segment is validated as its own evidence field and the fact
   grounds only if EVERY segment grounds. This loosens nothing — the same verbatim test runs
   once per segment, and a fact with an invented half still fails on that half.
2. **Whitespace before punctuation is collapsed.** Tag-stripping leaves a space where the
   markup was, so the Gothamist text extracts as `"$3,800 , far exceeding"` and no frozen
   span could match it. Applied identically to source and span; removes no word, reorders
   nothing. This was the entire cause of the one apparent `F13` failure.

## 3. Grounder V1 — result

| | |
|---|---|
| facts checked | 22 (every USED fact) |
| **GROUNDED** | **21** |
| UNGROUNDED | 0 |
| UNFETCHED | 1 — `F10` |

Sources fetched live: `S0` groundtruth.justin.work (15,413 chars, packet `2139e24c2918`),
`S1` gothamist.com (7,359 chars, packet `618bfa910636`). `S2` is a PDF and was not fetched.
`S3` (huduser.gov) returned **HTTP 403** — the same block the frozen manifest already
records against Dezeen.

**`F10` is UNFETCHED, not contradicted.** "HUD adopted the 30% standard in 1981, evolving
from a 25% threshold used in earlier public housing programs", plus the 1969 Brooke
amendment — the article's fifth paragraph. Its only cited source 403s us, so this run could
not re-verify it. The held-out report records it as one of three load-bearing external facts
independently checked before the freeze. Unverifiable in this run is not the same as false,
and it is not being reported as clean.

Runtime: 2.3s of fetching, 0 provider calls, $0.

## 4. Prose scan (diagnostic, not a boundary)

`scan_free_prose_field` is documented in `grounding.py` as DIAGNOSTIC ONLY and explicitly not
a grounding boundary. Five hits, and every one is an artifact rather than a finding:

- `US Department`, `Senator Edward Brooke`, `1981`, `1969` — all from `S3`, the source that
  403s. Not in the joined text because the text is not there to be in.
- `NYU Furman Center` — `S1` says "NYU**'s** Furman Center". The possessive was removed in
  repair 1 to satisfy `factual_surface_audit`, which flagged `NYU's` as an unapproved entity.
  Two blunt screens now disagree about the same string; the entity is in the source.

## 5. Fact Check — NOT RUN

`FactCheckMixin._run_web_fact_check(strict=True)` needs two credentials, and neither is
reachable from this machine:

- extraction calls CLIProxyAPI at `http://127.0.0.1:8317/v1` with `CLIPROXY_KEY` — the proxy
  is a user systemd service on trident; port 8317 is closed here and the key is unset;
- verification calls OpenRouter (Perplexity Sonar) with `OPENROUTER_API_KEY` — unset here.

Both live in `/srv/secrets/openclaw.env` on trident (`orchestrator/config.py:57`). Running
the stage there needs SSH, and `jascha@trident.tail630536.ts.net` currently answers with a
Tailscale re-authentication prompt, which is the owner's to complete.

Nothing was stubbed, and no result is being reported for a stage that did not execute.

Provider calls 0 · OpenRouter $0.

## 6. To finish it

On trident, from the repo checkout, with the branch at this commit:

```
python3 automation/heldout_factual_bridge.py --fact-check
```

`--fact-check` is accepted and currently reports the credential block; wiring it to
`_run_web_fact_check` is a few lines once the stage can actually run.
