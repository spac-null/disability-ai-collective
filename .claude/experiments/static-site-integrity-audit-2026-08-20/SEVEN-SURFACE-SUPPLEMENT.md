# Seven-Surface Audit Supplement — 2026-08-20

Status: SUPPLEMENT / COMPLETION to the static-site integrity audit (not a
competing or re-run audit). Integrates already-completed read-only findings
for the seven surfaces not covered in the original pass: `llms.txt`,
`humans.txt`, `feed.xml`, and the four persona feeds. The site was not
rescanned to produce this file — findings below are transcribed from the
completed review and re-stated in this audit's disposition taxonomy.

## Surfaces covered

1. `llms.txt`
2. `humans.txt`
3. `feed.xml`
4-7. Four persona feeds

## Findings

### CONTACT — RESOLVED 2026-08-20

Routing policy adopted (OD-8): `jascha@cripminds.com` = general/owner,
`editor@cripminds.com` = editorial/corrections, `email@jaschablume.nl` =
retired from public CripMinds surfaces. `llms.txt` was the only surface still
using the retired address; fixed. `about.html`, `jascha.html`,
`accessibility.html`, `press/index.html` already matched the policy.

### `humans.txt` — CLOSED 2026-08-20 (was P1 UPDATE_TRUST_DISCLOSURE)

The v3.1 milestone line previously read "Unsupported quotations, events, and
biographical details are rejected" as an unqualified present-tense claim.
Rewritten to "Current standard: unsupported quotations, events, and
biographical details are not permitted. Earlier work is reviewed against
this standard, not assumed to already meet it." No claim of retroactive
validation, no implication the new engine is already live.

### `llms.txt` — CLOSED 2026-08-20 (was P1 UPDATE_TRUST_DISCLOSURE)

The principle (interpretation may go beyond a source's conclusion; factual
premises may not be invented) is kept. The "Published Articles" section now
adds: "This is the standard current and future work is held to; earlier
archived work is reviewed against it, not assumed to already satisfy it in
every case." No internal codenames exposed.

### Research index claim — CORRECT, no finding

`/research/` claims and framing were checked against actual state and are
accurate. No finding; disposition KEEP.

### Feeds — 0 stale representation failures

`feed.xml` and the four persona feeds are generated from canonical post data
and were not found to misrepresent it. No P0/P1/P2 finding on feed content
itself.

Two low-severity items:

- **P3** — feed config contains inert/mismatched settings versus the
  hand-written `feed.xml` (config values that don't match what's actually
  emitted; cosmetic/config-hygiene, not a factual or trust problem).
- **P3** — the four persona feeds have no autodiscovery `<link>` tags and no
  public on-site references pointing to them. They exist and are correct but
  are effectively undiscoverable by readers or feed clients that rely on
  autodiscovery.

## Disposition summary for this supplement

| Surface | Disposition | Priority | Status |
|---|---|---|---|
| llms.txt | UPDATE_TRUST_DISCLOSURE | P1 | CLOSED 2026-08-20 |
| humans.txt | UPDATE_TRUST_DISCLOSURE | P1 | CLOSED 2026-08-20 |
| contact addresses (site-wide) | OWNER_DECISION | — | RESOLVED 2026-08-20 |
| /research/ index claim | KEEP | — | — |
| feed.xml | KEEP | — | — |
| persona feeds (×4) | KEEP (content) | — | — |
| feed config vs feed.xml mismatch | UPDATE_FACT | P3 | OPEN — Batch 2 |
| persona feed discoverability | UPDATE_ARCHITECTURE_DESCRIPTION | P3 | OPEN — Batch 2 |

The three P1/OWNER_DECISION items above were closed 2026-08-20 as part of
Batch-1 trust cleanup. The two P3 items remain **open** for Batch 2, along
with gallery noindex, Tumblr bio, sameAs metadata, accessibility-date
verification, and notes navigation — none of that was touched in this task.
