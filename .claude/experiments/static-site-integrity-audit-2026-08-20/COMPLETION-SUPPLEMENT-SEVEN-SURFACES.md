# Completion Supplement — Seven Uncovered Surfaces

**Status: this supplement is what makes the static-site audit COMPLETE.**

The original audit (commit `3242e50`) dispositioned **32 surfaces** and set
`audit_complete: true`. Seven public surfaces were absent from its audited set and
unmentioned in any of its findings documents. They are audited here and integrated into the
same deliverables; the totals in `inventory.json` have been adjusted mechanically rather than
leaving the earlier figure standing as final.

Identified by an independent cross-check from a parallel session. Only these seven were
audited — no already-audited surface was rescanned.

| # | Surface | Public URL | SHA-256 (at audit) |
|---|---|---|---|
| 1 | `llms.txt` | `/llms.txt` | `b6c589383800cb74…` |
| 2 | `humans.txt` | `/humans.txt` | `257ce6d68ed93659…` |
| 3 | `feed.xml` | `/feed.xml` | `efc5c84865b85613…` |
| 4 | `feed-maya-flux.xml` | **`/feed/maya-flux.xml`** | `c0bd42afb117f985…` |
| 5 | `feed-pixel-nova.xml` | **`/feed/pixel-nova.xml`** | `d0b51a48c52421f4…` |
| 6 | `feed-siri-sage.xml` | **`/feed/siri-sage.xml`** | `b87f5cb15beb6194…` |
| 7 | `feed-zen-circuit.xml` | **`/feed/zen-circuit.xml`** | `f9004afd80e21c5f…` |

Note the persona feed URLs come from a `permalink:` in each file — they are served at
`/feed/<persona>.xml`, **not** at the source filename.

---

## S-1 · Contact address conflict — P2 · `OWNER_DECISION`

Three different contact addresses are published across the static site.

| Address | Appears on | Apparent role |
|---|---|---|
| `jascha@cripminds.com` | `jascha.html`, `accessibility.html`, `press/index.html`, and `humans.txt` (as `jascha [at] cripminds.com`) | general / accessibility / press contact |
| `editor@cripminds.com` | `about.html`, framed as *"Questions, corrections, responses to published work"* | editorial corrections |
| `email@jaschablume.nl` | `llms.txt` (contact section) | machine-readable contact for AI agents |

Two of the three are plausibly a deliberate split (personal vs editorial). The third,
`email@jaschablume.nl`, reads like a placeholder — its local part is literally the word
`email`, and it points at a different domain from every other contact on the site.

**No repo or runtime evidence establishes a canonical public address**, so this is not
resolved here and no address is assumed correct. A corrections-focused address that is wrong
or unmonitored is a trust problem, which is why this is P2 rather than cosmetic.

Bounded cross-check performed (justified because the finding originates in `llms.txt` but
spans other surfaces): all `mailto:` and address strings on public surfaces were enumerated.
`your@email.com` also appears ×4 — those are form placeholders in `_includes/subscribe-form.html`
and are correct as-is.

**Owner decision required:** which address is canonical, whether the personal/editorial split
is intended, and whether `email@jaschablume.nl` should be corrected or removed.

---

## S-2 · `humans.txt` trust guarantee — P1 · `UPDATE_TRUST_DISCLOSURE`

Current text, in the public milestones block:

> **v3.1  Aperture  2026-08-07** — Editorial review and factual grounding strengthened.
> **Unsupported quotations, events, and biographical details are rejected.**

Stated as a completed historical fact about the publication.

**Problem.** The canonical legacy-corpus state is **LC1 — MATERIAL LEGACY CREDIBILITY RISK**,
with 60–100 of 142 articles scoped as needing remediation and confirmed prior unsupported
biographical and factual material. Two P0 corrections were published on 2026-08-20
(`70d9292`, `86a91d3`) precisely because unsupported claims about a real named person had been
live since June. A milestone dated 2026-08-07 asserting that such material *is rejected* reads
as a guarantee over the existing corpus that the corpus does not support.

**Not rewritten here.** The eventual wording must distinguish an **editorial standard going
forward** from a **demonstrated guarantee about already-published work**. The standard itself
is not in question.

---

## S-3 · `llms.txt` trust guarantee — P1 · `UPDATE_TRUST_DISCLOSURE`

Current text, closing the "Published Articles" section:

> Articles are original essays indexed at /research/. They are published through four
> recurring fictional voices. **Interpretation may go beyond a source's conclusion; factual
> premises may not be invented.**

**Context matters here.** The sentence sits immediately after a description of the live system
and is written in the present tense, with no temporal qualifier, so it reads as a categorical
description of what the currently public corpus guarantees — in a file specifically addressed
to machine consumers, which will treat it as a factual assertion about the corpus.

**The principle is right and must not be erased.** The defect is **present-tense /
provenance ambiguity**, the same class as S-2: an editorial rule presented as an achieved
property of everything already published.

Also note `llms.txt` carries no engine or architecture claim — it describes a "private working
method called the Mind Engine" whose "exact mechanics are not public documentation." That
correctly avoids implying the new SOFA/Article Form/Writer Grounding architecture is live.
**No architecture-truth finding.**

---

## S-4 · `/research/` index claim — **CORRECT, no finding**

`llms.txt` states articles are *"indexed at /research/"*. The handoff flagged this as a
suspected error. **It is not one.**

Verified: `research.html` renders `<h1>Articles</h1>`, iterates `site.posts`, and is served at
`/research/`. It is the canonical article index, alongside four research-thread pillar cards.
The claim is accurate. Recorded explicitly so the suspicion is not re-raised later.

---

## S-5 · Feed representation integrity — **0 failures** · `KEEP`

The Swan Care standing rule — *a rebuilt, retitled, corrected or withdrawn article may leave
stale representations outside its own body* — was applied to all five feeds.

**All five feeds are fully generated from canonical post data at build time.** Every
article-derived field comes from Liquid, never from hand-maintained copy:

| Field | Source |
|---|---|
| item title | `{{ post.title }}` |
| item description | `{{ post.content \| strip_html \| truncatewords: 50 }}` (`feed.xml`) or `{{ post.excerpt \| strip_html }}` (persona feeds) |
| item link / guid | `{{ post.url \| absolute_url }}` |
| creator | `{{ post.author }}` / a literal matching the feed's own persona |
| categories | `{{ post.categories }}` |

Persona feeds select with `{% assign author_posts = site.posts | where: "author", "<Persona>" %}`.

**Consequence: a stale article representation is structurally impossible in these feeds.** The
2026-06-19 Swan Care article was retitled on 2026-08-08 and its feed entry followed
automatically — which is exactly the failure mode that *did* occur in `research/care-labor.html`,
where the card copy was hand-maintained. This is a useful contrast for the standing rule:
**generated surfaces self-heal; hand-maintained cards do not.**

The only hand-maintained copy in the feeds is each channel's own `<title>` and `<description>`.
All four persona descriptions correctly frame the voice as *"a fictional … editorial voice"* —
consistent with `llms.txt` and `humans.txt`, with no provenance overclaim. **KEEP.**

---

## S-6 · `feed.xml` configuration mismatch — P3 · `UPDATE_FACT`

`_config.yml` enables the `jekyll-feed` plugin and configures it:

```
feed:
  path: feed.xml
  template: feed.xml
  limit: 20
  description: "Essays that use disabled ways of seeing to uncover what ordinary subjects are really doing"
```

But a hand-written `feed.xml` exists at the same path and is what actually ships. It uses
`limit:10`, and its `<description>` is `{{ site.description }}` — *"Experimental editorial
publication asking what disabled ways of seeing can reveal…"*.

So the `feed:` block's `limit`, `description`, `author` and `categories` are **inert**: the
site publishes 10 items with a different description than the config declares. Two different
site descriptions exist in the repo and only one is served.

Low reader impact, which is why it is P3 — but it is a real config-versus-reality drift, and
the kind that misleads the next person editing `_config.yml` expecting it to take effect.

---

## S-7 · Persona feed discoverability — P3

`_layouts/default.html` publishes one autodiscovery link, for `/feed.xml` only. The four
persona feeds at `/feed/<persona>.xml` have:

- no `<link rel="alternate">` in any layout
- no reference from `_collective/*.md`, the collective pages, or any other public surface

Verified by search across all public HTML/Markdown/text. They are live and correct but
effectively unreachable except by guessing the URL. Not broken — undiscoverable.

Whether to surface them (e.g. from each persona page) is an editorial choice, not a defect.

---

## Adjusted totals

| | Original (`3242e50`) | Supplement | **Final** |
|---|---|---|---|
| Surfaces dispositioned | 32 | +7 | **39** |
| P0 | 0 | +0 | **0** |
| P1 | 1 | +2 | **3** |
| P2 | 1 | +1 | **2** |
| P3 | 3 | +2 | **5** |
| P4 | 3 | +0 | **3** |
| KEEP | 18 | +4 | **22** |
| UPDATE_FACT | 2 | +1 | **3** |
| UPDATE_TRUST_DISCLOSURE | 1 | +2 | **3** |
| OWNER_DECISION | 6 | +1 | **7** |

New findings: **2 × P1, 1 × P2, 2 × P3, 0 × P0.** Feed representation failures: **0**.

## Cleanup batch placement

- **BATCH 1 (Truth/Trust):** S-2, S-3 — the two present-tense trust guarantees.
- **BATCH 2 (Freshness/Representation):** S-6 feed config drift; S-1 once the owner names the canonical address.
- **BATCH 3 (Positioning):** S-7 persona feed discoverability, if wanted at all.

No cleanup performed in this supplement.

---

## Manifest integrity (verified 2026-08-20)

All seven new `SHA256SUMS.txt` entries were verified against the working tree —
**7/7 match**, so the appended hashes are computed, not transcribed.

A full `shasum -a 256 -c` over the whole manifest reports exactly **two**
mismatches, both expected and fully explained:

| File | Manifest hash | Explanation |
|---|---|---|
| `robots.txt` | `4a9f8639…` | equals `BATCH1-PRESERVED-robots.txt.before` byte-for-byte |
| `_config.yml` | `be0f63e8…` | equals `BATCH1-PRESERVED-_config.yml.before` byte-for-byte |

These are the two files Batch 1 containment edited (defensive `Disallow` entries;
`calibration/`+`reader-lab/` build exclusions). The manifest was frozen
pre-containment, so it correctly records their pre-edit state and the preserved
`.before` copies corroborate it. **No unexplained manifest drift.**

## Counting-model caveat

The `counts` block in `inventory.json` tracks **findings**, not inventory rows.
This was already true pre-supplement: the rows tally `KEEP=26` while the block
states `KEEP=18`. The supplement deltas were applied under that same findings
model. The row-vs-findings ambiguity is **pre-existing** and was deliberately not
re-derived, because re-deriving every total would be a re-audit rather than an
integration.

## Exposure scope

Website exposure and public-repository exposure are distinct and are recorded
separately in `EXPOSURE-SCOPE-AND-GIT-STATE.md`. Summary: website **CLOSED**;
public repo current tree **OPEN**; public repo history **OPEN**; the claim
*"editorial mechanics remain private"* is **PARTIAL / NOT LITERALLY TRUE**
(`OWNER_DECISION`). No secrets found; no history rewrite authorized or attempted.

---

## Disposition status — updated 2026-08-20 (post Batch-1 trust deployment)

| Finding | Was | Now |
|---|---|---|
| **S-1** contact conflict (P2) | OWNER_DECISION, unresolved | **RESOLVED** as **OD-8**: `jascha@cripminds.com` general/owner, `editor@cripminds.com` editorial/corrections, `email@jaschablume.nl` retired from public surfaces (mailbox untouched). Zero public-surface occurrences remain. |
| **S-2** `humans.txt` guarantee (P1) | OPEN | **CLOSED** — v3.1 milestone now reads "Current standard: … Earlier work is reviewed against this standard, not assumed to already meet it." Standard preserved, corpus guarantee removed. Deployed and live-verified. |
| **S-3** `llms.txt` guarantee (P1) | OPEN | **CLOSED** — now states the current editorial standard and that "earlier archived work is reviewed against it, not assumed to already satisfy it in every case." Principle preserved; `/research/` index claim left intact per S-4. Deployed and live-verified. |
| **S-4** `/research/` claim | CORRECT, no finding | unchanged — **CORRECT** |
| **S-5** feed representation | 0 failures, KEEP | unchanged — **0 failures** |
| **S-6** `feed.xml` config drift (P3) | OPEN | **OPEN** → Batch 2 |
| **S-7** persona feed discoverability (P3) | OPEN | **OPEN** → Batch 3 (may be declined) |

Closed by content commit `98ea267`, deployed via run `32372116318`
(success, 2026-08-20 13:03Z). Both P1s were verified against the live site, not
only against the repo.

**Remaining from this supplement: two P3s, both deferred. No P0 or P1 open.**
