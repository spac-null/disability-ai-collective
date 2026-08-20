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

### CONTACT — OWNER_DECISION

Three distinct contact addresses appear across site surfaces, and no single
one is marked canonical:

- `jascha@cripminds.com`
- `editor@cripminds.com`
- `email@jaschablume.nl`

This audit does not assume which is canonical. Resolving this is an owner
decision — see `OWNER-DECISIONS.md`.

### `humans.txt` — P1 UPDATE_TRUST_DISCLOSURE

The current wording asserts a stronger historical/corpus guarantee than the
LC1 evidence-gathering work supports. It should be softened to a claim the
site can actually stand behind given the legacy corpus was produced under a
prior engine/process, not retroactively validated by current safeguards.

### `llms.txt` — P1 UPDATE_TRUST_DISCLOSURE

The principle stated — that factual premises should not be invented — is
correct and should be kept. The problem is the present-tense/provenance
framing: it reads as describing a guarantee that holds across the entire
public corpus today, which overstates what the legacy public corpus can
actually be shown to guarantee. Narrow the tense/scope, keep the principle.

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

| Surface | Disposition | Priority |
|---|---|---|
| llms.txt | UPDATE_TRUST_DISCLOSURE | P1 |
| humans.txt | UPDATE_TRUST_DISCLOSURE | P1 |
| contact addresses (site-wide) | OWNER_DECISION | — |
| /research/ index claim | KEEP | — |
| feed.xml | KEEP | — |
| persona feeds (×4) | KEEP (content) | — |
| feed config vs feed.xml mismatch | UPDATE_FACT | P3 |
| persona feed discoverability | UPDATE_ARCHITECTURE_DESCRIPTION | P3 |

These remain **open** — not executed in this task. They fold into Batch 1
trust cleanup as noted in `OWNER-DECISIONS.md` and are not to be started
until that document's remaining-items list is explicitly cleared.
