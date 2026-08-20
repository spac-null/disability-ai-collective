# Swan Care Legacy Incident — Cluster Closure

**Outcome: 0 withdrawals, 3 corrections, cluster closed.**
The finding that drove this task turned out to be wrong in one important respect, recorded
below rather than quietly worked around.

## The complete cluster

Every public item mentioning Swan Care or Shabin Shaji, checked against the already-preserved
tribunal written reasons (case 1308762/2023) rather than re-verified from scratch.

| # | Item | Verdict |
|---|---|---|
| 1 | `research/care-labor.html` | **CORRECT_WITH_DISCLOSURE** — P0 lede fixed earlier (`70d9292`); stale cards fixed here |
| 2 | `_posts/2026-05-30-nhs-lancashire-and-south-cumbria-recruited.md` | **CORRECT_WITH_DISCLOSURE** — false accommodation-as-wages cross-link |
| 3 | `_posts/2026-06-09-three-months-in.md` | **CORRECT_WITH_DISCLOSURE** — misdescribed the subject as a wheelchair user |
| 4 | `_posts/2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment.md` | **KEEP_AS_LEGACY** — supported by the record |
| 5 | `_posts/2026-06-19-swan-care-is-appealing-the-appeal-is-the-mechanism.md` | **KEEP_AS_LEGACY** — already rebuilt 2026-08-08 |
| 6 | `_posts/2026-06-20-i-use-care-workers-…md` | **KEEP_AS_LEGACY** — supported |
| 7 | `research.html`, `cripminds-stats-2026-06.html` | no action — title references only |

## The correction to my own earlier finding

The previous task reported that
`2026-06-19-swan-care-is-appealing-the-appeal-is-the-mechanism` was *"the strongest WITHDRAW
candidate in the corpus"*, because its title and thesis rested on an appeal that does not
exist. **That was wrong, and it was my error.** I read the index card, not the article.

The article was **already rebuilt on 2026-08-08** — commit `7c4719d`,
*"fix: rebuild second Swan Care article — its entire thesis was fabricated"*. Its title was
changed from *"Swan Care Is Appealing. The Appeal Is the Mechanism."* to
**"Winning the Case Does Not Turn Off the Clock"**, and its argument is now visa curtailment
when a sponsor licence is revoked — two systems, one worker — which the tribunal record and
press coverage support. The only occurrences of "appeal" left in it are three asset filenames
derived from the old slug.

What was actually broken was the **index**: `research/care-labor.html` was never updated when
the article was rebuilt, so for twelve days it presented the withdrawn title and an
appeal-based description as a normal current article, in both the visible card and JSON-LD.

**No withdrawal was required.** The article that would have been withdrawn had already been
fixed; the stale pointer to it had not.

## Frozen fact record

One record, used for all articles — not re-derived per item. Source:
`legacy-p0-care-labor-correction-2026-08-20/preserved/tribunal-1308762-2023-written-reasons.txt`
(sha256 `910c1bd6…`), plus Guardian and Work Rights Centre coverage.

**SUPPORTED**

- Case 1308762/2023, *Mr S Shaji v Swan Care Solutions Ltd and E Chengeta*
- Heard 2–4 March 2026, Birmingham, Employment Judge Edmonds; judgment sent to the parties 5 March 2026
- Certificate of sponsorship: start 27 February 2023, 40-hour week, £22,880 gross per annum
- Employed 15 April 2023 – 21 April 2024
- *"the claimant was ready, willing and able to perform his duties, and the only reason he did not do so was because the respondent did not provide him with work"*
- Awards: £20,400.76 net unauthorised deductions · £2,168.85 net holiday pay · £4,080.15 + £433.77 uplift · £1,760 (four weeks' gross) — £28,843.53 total
- A "withdrawal of" letter dated 27 December 2023 which the tribunal found *"did not exist as at 27 December 2023"*
- The respondent's sponsorship licence was *"ultimately revoked in 2024, in part precisely because"* of this pattern
- £17,000 paid to a recruitment agent (press)
- Represented by Work Rights Centre (press)

**NOT SUPPORTED**

- £5/hour — no hourly rate appears anywhere in the decision; he was paid nothing
- accommodation/housing deducted from wages — no such finding
- Swan Care appealing — the word "appeal" does not appear in the decision, and no appeal is in any published report
- judgment in June 2026 — it was 5 March 2026
- **new, found in this pass:** the subject described as a wheelchair user — he is a migrant care worker

**NOT DISPROVEN, and treated as such:** two press-sourced specifics in the 06-04 article — the
"tap water and bread close to its expiration date" quote, and the *"roughly 39,000 care workers
… across 470 revoked sponsorships"* statistic. Absence from the judgment is not disproof; the
article cites Guardian Society. Logged as MEDIUM-risk items for the LC1 backlog, **not** Swan
Care falsehoods.

## What changed

3 files, **18 insertions / 10 deletions**. Full diff: `cluster-fix.diff`.

| File | Change |
|---|---|
| `2026-05-30-…` | *"classified a migrant care worker's accommodation as wages … his need to sleep treated as a deductible cost"* → the zero-hours finding, plus a correction note |
| `2026-06-09-…` | *"a wheelchair user classified as equipment travels"* → *"a named worker given zero hours for a year travels"*, plus a correction note |
| `research/care-labor.html` | 06-19 card retitled to the real title with a new description and a note that the URL keeps the original slug; 06-04 card's shelter/deductible framing replaced; JSON-LD `itemList` name corrected; the earlier "under review" line resolved |

No style modernisation, no unrelated interpretation touched, no article rewritten through the
new engine, no URL changed.

## The URL that still asserts the claim

`/2026/06/19/swan-care-is-appealing-the-appeal-is-the-mechanism/` still carries the
pre-rebuild slug. It was **deliberately left alone**: renaming it would break the canonical
record, any inbound links, and the article's own asset paths, to fix a slug on an article
whose content is now correct. The index card discloses it explicitly. Changing it is an owner
decision, not a factual necessity.

## Verification

| Check | Result |
|---|---|
| Only 3 intended files changed | ✔ |
| No `permalink` / `date` / `url` line changed | ✔ all URLs stable |
| JSON-LD parses | ✔ |
| Tag balance in the index | ✔ `p` 13/13, `div` 10/10, `a` 8/8, `h2` 5/5 |
| Markdown front matter intact on both posts | ✔ |
| Pages deploy | ✔ run `32368084791`, **success**, 55s |
| Live `research/care-labor/` | ✔ old appeal title gone; "Winning the Case…" ×2; shelter framing gone |
| Live `2026/05/30/…` | ✔ corrected sentence + note; the one "accommodation as wages" hit is inside the note |
| Live `2026/06/09/…` | ✔ "wheelchair user classified as equipment" gone |
| Live `2026/06/19/…` | ✔ title reads "Winning the Case Does Not Turn Off the Clock" |

## Social

`_social/` records Bluesky URIs only. **One post exists in the entire cluster:**

| Article | Post | Action |
|---|---|---|
| `2026-06-04-swan-care-solutions-ltd-classified-someone-as-equipment` | `at://did:plc:4x2xhho3ozmrknpxqbdjtmbv/app.bsky.feed.post/3mnh2k2ymo22v` (Zen Circuit) | **NO_ACTION** |

It promotes the article that is **accurate**. Nothing was withdrawn, so no promotional post is
circulating an invalidated claim. The other five items have no recorded post. No X, Reddit,
LinkedIn or Facebook records exist in the repo.

**No social modification performed, and none required.**

## Isolation

Publish used the same discipline as the P0: local `main` was 36 commits ahead of origin with
`.claude/` evidence never intended for deployment, so the content commit was cherry-picked
onto `origin/main` and pushed alone — `70d9292..86a91d3`, verified to contain **zero** `.claude/`
files before pushing.

Phase-2 capture flag, article cron, publication selector, AR3, Writer Grounding and production
prompts untouched.
