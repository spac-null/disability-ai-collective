# Legacy Corpus P0 — care-labor factual correction

**Scope: this one confirmed finding. Not a new audit. No rescan of 142 articles.**

Identified by the existing `.claude/legacy-corpus-integrity-phase1-2026-08-16.md`
(+ `audits/legacy-corpus-integrity-2026-08-16.json`), which flagged it on 2026-08-16 as
**"HIGHEST-SEVERITY FINDING IN AUDIT"**. It had been public since then.

## The article

| | |
|---|---|
| Path | `research/care-labor.html` |
| Public URL | `https://cripminds.com/research/care-labor/` (**unchanged**) |
| Pre-correction sha256 | `9e2f89a87a3163b5cbfe3ddaa4569a829d6969736586967ea881fcad5e5a59fb` |
| Preserved copy | `preserved/care-labor.html.pre-correction` |
| Git history | `9734b99` (2026-06-14, created) · `e4746db` (2026-08-12, metadata) |
| Real person named | Shabin Shaji |
| Real company named | Swan Care Solutions Ltd |
| Real case | UK employment tribunal **1308762/2023** |

## Confirmed errors — four, not three

Verified against the **primary source**: the tribunal's own written reasons
(`preserved/tribunal-1308762-2023-written-reasons.txt`, sha256
`910c1bd6570c0a5a1be5e1e215adfcbc3d5315eb4093f4867b45915c3b359092`, retrieved from
`assets.publishing.service.gov.uk`), cross-checked against Guardian and Work Rights Centre
reporting.

| Claim as published | Status | Evidence |
|---|---|---|
| "He was paid £5 an hour" | **FALSE** | Zero matches for `£5`, `per hour`, `hourly`, `an hour` anywhere in the decision. He was paid nothing at all |
| "His housing was deducted as wages" | **FALSE** | No accommodation deduction from wages is found. "Accommodation" appears only in narrative about where he arranged to live before starting |
| "Swan Care is appealing" | **UNSUPPORTED** | The word "appeal" does not appear in the decision, and no appeal was found in any published report |
| "In June 2026" | **FALSE** | Heard 2–4 March 2026; judgment sent to the parties **5 March 2026** |

The fourth error was not in the Phase-1 finding; it surfaced while verifying the other three.

## What the record actually says

- Certificate of sponsorship: start 27 February 2023, **40-hour week, £22,880 gross per annum**
- Employment ran **15 April 2023 – 21 April 2024**
- *"the claimant was ready, willing and able to perform his duties, and the only reason he did
  not do so was because the respondent did not provide him with work. The respondent withheld
  work from him"*
- The tribunal therefore treated **the full gross salary** for that period as an unauthorised
  deduction from wages
- Awards: **£20,400.76 net** (unauthorised deductions) · **£2,168.85 net** (holiday pay) ·
  **£4,080.15** + **£433.77** (20% uplift) · **£1,760** (four weeks' gross pay)
- Press additionally reports the Home Office revoked the company's sponsorship licence

The truth is worse than what was published: not underpayment, but a year of withheld work and
withheld pay under a sponsorship visa.

## Remediation: CORRECT_WITH_DISCLOSURE

Chosen because the page's central argument — the health and care visa as a sponsorship trap —
**survives and is strengthened** by the real record. The false specifics were local to the
lede and metadata, not load-bearing for the thesis.

`WITHDRAW` was not warranted for this page.

### Exact change — 18 insertions, 5 deletions, one file

1. Front-matter `description` — rewritten to the record
2. JSON-LD `description` — same
3. Lede — the four false assertions replaced with the sponsorship terms, the withheld-work
   finding, and the award
4. Body clause "the appeal as attrition," → "the year of withheld work and withheld pay,"
   (it presupposed an appeal that is not in the record)
5. Visible correction note added

**Correction note as published:**

> **Correction, 20 August 2026:** An earlier version of this page stated that Shabin Shaji was
> paid £5 an hour, that his housing was deducted from his wages, that the tribunal decision
> came in June 2026, and that Swan Care Solutions was appealing. None of these are supported by
> the tribunal record (case 1308762/2023, heard 2–4 March 2026, judgment sent to the parties on
> 5 March 2026). The tribunal found that the respondent never provided the claimant with work
> and never paid him, and awarded him unpaid wages and holiday pay. No appeal is recorded in
> the tribunal decision or in any published report of the case. The two articles linked below
> repeat the same unsupported claims and are under review.

It states what changed, does not describe internal architecture, and does not claim the page
has been retrospectively validated.

### What was NOT done

No rewrite through the new engine · no stylistic modernisation · no unrelated prose touched ·
URL unchanged · no other file modified.

## Verification

| Check | Result |
|---|---|
| Only the intended file changed | ✔ 1 file |
| No changed line touches `permalink` or `url` | ✔ URL stable |
| Front matter YAML parses | ✔ `permalink: /research/care-labor/` |
| JSON-LD parses | ✔ |
| Tag balance (`p`/`section`/`div`/`main`) | ✔ all balanced |
| Residual false claims in page voice | ✔ 0 (the one `£5 an hour` hit is inside the correction note, quoting the earlier version) |
| Pages deploy | ✔ run `32367255606`, **completed success**, 1m7s |
| Live page carries the correction | ✔ verified via `curl` |

## THE PROBLEM IS WIDER THAN THIS PAGE — flagged, not fixed

This page is an index. The same unsupported claims are asserted by **published articles**:

| Item | Status |
|---|---|
| `_posts/2026-06-19-swan-care-is-appealing-the-appeal-is-the-mechanism.md` | **P0.** The entire article, including its title, is built on an appeal that is not in the record. This is the strongest `WITHDRAW` candidate in the corpus |
| `_posts/2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment.md` | **P0.** Subtitled "a deductible business expense" — the housing-deduction claim. Has a recorded Bluesky post |
| `_posts/2026-06-09-three-months-in.md` | Repeats a Swan Care claim as settled fact (noted in the Phase-1 manifest, `articles[90]`) |

The live page still shows the appeal article's own title in a link card. That is disclosed in
the correction note rather than hidden — this page cannot rename another article.

## Social promotion

| Article | Record |
|---|---|
| `2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment` | Bluesky `at://did:plc:4x2xhho3ozmrknpxqbdjtmbv/app.bsky.feed.post/3mnh2k2ymo22v` (agent: Zen Circuit) |
| `2026-06-19-swan-care-is-appealing-…` | no `_social/` record |
| `research/care-labor.html` | no `_social/` record (static pages are not auto-promoted) |

`_social/` tracks Bluesky URIs only. **No X, Reddit, LinkedIn or Facebook records exist** in
the repo for these items.

**No social modification performed.** The corrected page is the canonical correction record.
Follow-up becomes high priority if the 2026-06-19 article is withdrawn.

## Isolation

Phase-2 capture flag, article cron, publication selector, AR3, Writer Grounding, production
prompts and the new architecture were **all untouched**. Trident tracked-clean throughout;
capture still enabled; 0 capture bundles (sample still 0/3).
