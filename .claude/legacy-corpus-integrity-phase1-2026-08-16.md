# CripMinds Legacy Corpus Integrity Audit — Phase 1

**Date:** 2026-08-16
**Type:** Diagnosis only. No articles rewritten, unpublished, or altered. No public copy changed. No deploy.
**Machine-readable manifest:** `.claude/audits/legacy-corpus-integrity-2026-08-16.json`

Method note: every count below is derived from the current repository tree, current Jekyll `_config.yml` build/exclude rules, and git commit history — not from prior assumptions. The previously-assumed "~141 articles" figure was checked and is superseded by the number below.

---

## 1. PUBLIC INVENTORY

Confirmed by reading `_config.yml`'s `collections:`/`exclude:` rules directly, not by assuming every file under a plausible-looking directory is public.

| Type | Count | Notes |
|---|---|---|
| **Articles** (`_posts`, collection `posts`, output: true) | **142** | permalink `/:year/:month/:day/:title/` |
| **Static/institutional pages** | **20** | about, index, accessibility, research (index), notes, collective (stub), jascha, humans.txt, llms.txt, press/, press/how-it-works/, 4× `research/*.html` topic pages, 404, gallery |
| **Persona (Collective) pages** | 4 | `_collective/*.md` → `/collective/<name>/`, collection `collective`, output: true |
| **Works** | 1 | `_works/what-the-room-heard.html` → `/works/what-the-room-heard/`, collection `works`, output: true |
| **Debates** | 0 | `_layouts/debate.html` exists but is used by zero content files — dormant scaffolding, not a live public content type |
| **Total public items** | **162** | 142 articles + 20 static/institutional (the persona pages and Work are counted inside the 20) |

**Confirmed NOT public**, despite living in the repo and in several cases looking like they should be (checked against `_config.yml` `exclude:` and per-file `published: false` front matter, not assumed):

- `accessibility/` (46 files) — the site's own accessibility **self-audit reports**, excluded from build. Distinct from the public `accessibility.html` statement page.
- `_research/` (10 files) — internal research logs / `stats.json`. Not a configured Jekyll collection. Distinct from the public `research.html` index and `research/*.html` topic pages, which **are** public — this is an easy thing to conflate and worth flagging so it isn't miscounted in future audits.
- `_social/` (127 files) — Bluesky cross-post automation artifacts (post URIs). Not referenced by any layout/page; not served by the site.
- `_reviews/` (134 files) — the existing citation-audit trail. Not a Jekyll collection, not reader-facing, but used throughout this audit as prior-review/source-recoverability evidence.
- `_drafts/` (6 active + 13 archived) — standard Jekyll drafts, never built without `--drafts` (confirmed absent from the build tooling). Includes 4 pieces the **current fact-check gate correctly BLOCKED** before publication — a positive signal the current pipeline works.
- `MANIFESTO.md`, `PIPELINE.md`, `SCRAPING_ETHICS.md`, `README.md`, `requirements.txt`, `cripminds-stats-2026-06.html` — explicitly listed in `_config.yml`'s `exclude:`.
- `editorial-lens.md`, `style-lab.html`, `realistic-scenes.html` — `published: false` in front matter.

Full detail on each excluded item, including content-risk notes for the ones that would need grounding *before* ever being published, is in the JSON manifest under `excluded_from_public_build_but_considered`.

---

## 2. PRODUCTION ERAS

Derived from actual commits, not invented date buckets:

| Era | Date range | What changed | Articles published in this era |
|---|---|---|---|
| **A — pre-guardrail** | 2026-03-08 to 03-13 | No citation/grounding review existed yet at publish time (first reviews were backfilled 2026-03-14, commit `09f21e5`, for "8 published articles") | 6 |
| **B — citation guardrail** | 2026-03-14 to 08-05 | Per-article heuristic citation review exists at publish time; no web verification yet | 131 |
| **C — web fact-check** | 2026-08-06 to 08-08 | Real web-search verification of named quotes (`2f97a08`), graduated blocking for stats/studies/events (`6b69777`, `d5adb7f`) | 4 |
| **D — Phase 1.6 grounding hardening** | 2026-08-09 to 08-13 | Evidence-packet source-hash design, legacy-brief rejection policy (`bdfcb34`…`8be32e0`) | 1 |
| **E — human-detail provenance shadow guard** | 2026-08-14 | `91b8da3` | 0 published (applies to drafts currently in the pipeline) |
| **F — author-persona biography provenance safety (current)** | 2026-08-15 to 08-16 | `a73d71a`, `dbe0a96` | 0 published |

Two things worth naming explicitly: **131 of 142 articles (92%) were produced under Era B**, the heuristic-citation-only regime — this is the era that matters most for remediation sizing. And **Eras E and F, the newest and most relevant safeguards for exactly the risk this audit found most, have not yet reached any published article** — they exist in the pipeline but the most recent live article (2026-08-11) predates them. The team appears to already be aware of and actively working the class of problem this audit surfaces (see `.claude/author-persona-biography-provenance-2026-08-14.md`, `.claude/human-detail-provenance-and-source-completeness-2026-08-14.md`) — this audit's job is to quantify how much of the *already-published* corpus is affected, since those fixes are forward-looking only.

---

## 3. STATIC COPY

**RISK COUNTS (20 items assessed): 17 GREEN / 4 AMBER (`jascha.html`, `humans.txt`, `press/index.html`, `press/how-it-works/index.html`) / 1 RED (`research/care-labor.html`)**

### Highest-risk finding in the entire audit
`research/care-labor.html` names a **real, identifiable individual** (Shabin Shaji) and a **real named company** (Swan Care Solutions Ltd) in connection with a genuine UK employment tribunal case (1308762/2023, independently confirmed via the gov.uk tribunal decision, Guardian coverage, and Work Rights Centre reporting). But the article's specific claims — "paid £5 an hour," "his housing was deducted as wages," "Swan Care is appealing" — **do not match the real record**, which concerns the employer providing **zero hours/zero pay** for roughly a year under a sponsorship visa promising 40hrs/week at £22,880/year (≈£37,643 awarded for hours the claimant was "ready, willing and able" to work). No appeal was found in any source. This is a real, named, non-fictional third party — a categorically different and more serious risk than the disclosed-fiction persona findings elsewhere in this audit.

### Second finding: the site's own stated policies are contradicted by its own content
`humans.txt` ("Unsupported quotations, events, and biographical details are rejected") and `press/how-it-works/index.html` ("No invented factual floor... if support cannot be found, the claim is removed or clearly marked as uncertain") both state an editorial guarantee that `research/care-labor.html` currently violates. This is an internal-consistency failure independent of the underlying facts, and elevates the care-labor finding from "one bad article" to "the site is not currently living up to a promise it makes to readers and press."

### Lower-severity findings
`jascha.html` and `press/index.html` (the real founder's own biography, used for press purposes) contain two named/dated artworks ("De Gebarentaaltolk en Ik," "Retrieve My Time," 2010) that could not be independently verified — plausible given the artist's real documented practice, but unverified, and repeated at length on the page journalists are most likely to cite directly.

`_collective/*.md` (all 4 persona bios), `about.html`, `index.html`, `llms.txt`, `accessibility.html`, `research.html`, and the 3 non-`care-labor` `research/*.html` topic pages were all GREEN — clean fictionality disclosure, or well-supported real-world scholarship (Jim Sinclair 1993, Baron-Cohen, Hendrick Avercamp, Joseph Grigely's ~120,000-scrap archive, Christine Sun Kim).

`_works/what-the-room-heard.html` is worth naming as a **positive counter-example**: explicit `provenance_summary` front matter classifying each element (Document / Reconstruction / Simulation), a documented CC0 rights-closure history (`.claude/cripminds-what-the-room-heard-rights-closure-2026-08-15.md`), and an unconfirmed causal detail explicitly labeled unconfirmed rather than asserted. This is what the target state looks like.

---

## 4. ARTICLE CORPUS

**Total: 142.**

### Structural-scan distribution (mechanical signal only — front matter + existing `_reviews` flags + regex pass for quotes/numbers/first-person markers/causal language; NOT a semantic verdict)

| Signal | Count |
|---|---|
| RED (≥10 prior flags, or unresolved and quote/personal-history heavy) | 24 |
| AMBER (some flags, or no review file at all, or 1–9 flags) | 107 |
| GREEN (CLEAN status, zero flags) | 11 |

**Important finding independent of content:** existing `_reviews/*.md` are not reliable as-is. Of the 20 articles semantically re-read for this audit, **8 (40%) had a review file that no longer matches the live article** — the review audited an earlier draft (specific dollar figures, quotes, named sources, even entire anecdotes present in the review text are simply absent from the current published text, and vice versa). This means "has a review file" and "review says CLEAN" are **not trustworthy proxies for current risk** without re-verification against the live file. Treat every review-status number in this report as an upper bound on *documented* concern, not a lower bound on *actual* concern.

### Source recoverability

| Category | Count |
|---|---|
| SOURCE_PACKET_AVAILABLE (source_url + title + outlet in front matter — current single-source pipeline) | 85 |
| PARTIAL_SOURCE_HISTORY (a review file exists, documenting *something*, but no actual source recovered) | 18 |
| SOURCE_TEXT_RECOVERABLE (review references named/dated sources not yet fully resolved) | 16 |
| NO_RECOVERABLE_SOURCE (no review file, no source_url) | 23 |

**32 of 142 published articles (22.5%) have no citation-review file at all.** This is not confined to the earliest pre-guardrail week — it recurs sporadically from 2026-03-14 through 2026-08-08, including days where a sibling article published the same day *did* get reviewed. In June and July alone, 56 articles were published against only 33 review files. This is an ongoing audit-trail gap, not a one-time legacy artifact.

---

## 5. SEMANTIC SAMPLE

**Method:** 20 articles (14% of the corpus), deliberately stratified rather than randomly drawn, per the brief's instruction to prioritize risk-flagged material: all 6 pre-guardrail-era (Era A) articles; 4 no-review-gap articles across the timeline; the 4 highest-flag-count articles; 4 articles with `CLEAN` prior-review status as controls; and 2 structural outliers (unusually high quote density, unusually high first-person-history density). Two independent read-throughs were run in parallel, each also spot-verifying real-world claims via web search where checkable.

**Result: 10 RED / 7 AMBER / 3 GREEN.**

Because the sample deliberately over-weighted risk-flagged subpopulations, a 50% RED rate is not directly a random-sample estimate for the full 142. What *is* directly informative: **3 of the 4 "CLEAN"-status control articles turned out to have real, previously undetected issues** on independent re-read (a fabricated dated professional anecdote in one; a wrong exhibition date for a real artist/institution in another; a title/body statistic that had silently drifted from the reviewed draft in a third). Only 1 of 4 CLEAN controls held up. That is the single most load-bearing data point for estimating the *true* baseline rate across the unsampled 122 — it suggests the mechanical/CLEAN signal substantially understates real risk across the whole corpus, not just the visibly-flagged subset.

### Representative failure modes found

- **Invented dated personal-history testimony**, the single most common and highest-value-missed pattern: specific real-institution-plus-date first-person claims (a Rotterdam hospital consulting engagement in Feb 2024, a Brussels transit design review in Nov 2021, visits to the Barbican in Sept 2019 and the Stedelijk in June 2018, a named psychologist's-office diagnosis scene dated January 2016) presented as real autobiography. The existing automated citation scanner **consistently misses every one of these** — it's tuned for database-checkable facts, not first-person historicity, and none of the semantic-sample findings of this type had been previously flagged.
- **Named real individuals given unconsented anecdotes/quotes** inside articles, distinct from the disclosed fictional personas: "Sarah" (job-accessibility anecdote), "Mara" (named colleague, direct quotes), "Leo"/"Javier" (disability disclosure), and a named real professional, Shira Wakschlag of The Arc, paraphrased/quoted on Hurricane Milton shelter turnaways with no outlet or date cited.
- **Fake-looking citations**: one article hyperlinks a named individual's disability disclosure to literal `example.com` placeholder URLs — a fabricated *appearance* of sourcing, a distinct and more concrete defect than merely being uncited.
- **Recycled/templated statistic**: the figure "1,247 barriers" appears attached to two different Maya-Flux-persona studies in two different cities in two different articles — evidence the number was reused rather than independently derived either time.
- **Real institutions given uncited precise figures**: a transit agency's (CTA) "96.2% elevator reliability" and Kusama's Tate Modern retrospective misdated by two years — both easily checkable, both wrong or unsupported as stated.
- A genuine positive: `_posts/2026-06-17-camouflaging-is-not-a-skill.md` — no review file, but also no invented studies, stats, named individuals, or personal-history claims; argumentative interpretation over well-established real research, correctly not flagged for lacking a citation per the taxonomy's own instruction.

---

## 6. SYSTEMIC PATTERNS

1. **The automated citation scanner has a structural blind spot for first-person testimony**, independent of era — it catches uncited *external* facts (which are usually accurate, just uncited) and almost never catches invented *personal* history, because that isn't a database-checkable claim. This is the single biggest driver of undercounted risk in this audit.
2. **Review staleness** — ~40% of sampled review files no longer describe the live article — is a distinct process-integrity problem, separate from content risk, and affects both flagged and CLEAN-labeled articles.
3. **Persona-level clustering, not era-level clustering**: the clearest content-fabrication pattern found (the recycled "1,247" statistic) tracks to one persona voice (Maya Flux) across articles in different eras, suggesting the pattern is about a narrative device/prompt habit rather than a single bad time period.
4. **Named-real-person risk is cross-cutting**, appearing in both the article corpus (multiple personas) and the static institutional copy (`research/care-labor.html`), and is categorically more serious than persona-anecdote risk because it touches identifiable third parties rather than disclosed fiction.
5. **The no-review-gap (32 articles) is chronic, not a one-time early-days artifact** — it recurs through early August.
6. **The corpus's stated safeguards and its content disagree with each other** in at least one confirmed instance (`humans.txt` / `press/how-it-works` vs. `research/care-labor.html`) — a finding about institutional credibility, not just article quality.
7. **The team is already aware of, and actively remediating, the general class of problem this audit is most concerned about** — the two most recent pipeline commits (Aug 14–15, human-detail provenance shadow guard; author-persona biography provenance safety) target exactly the invented-personal-history pattern found repeatedly in this sample — but those safeguards are forward-looking only and have not yet touched any of the 142 already-published articles.

---

## 7. CREDIBILITY ASSESSMENT

This is a **material legacy credibility risk**, not primarily a style problem. Three lines of evidence converge: (a) a confirmed RED finding involving a real, named, identifiable third party and real company, where the site's own published claims about a public tribunal case do not match the actual record; (b) a direct contradiction between the site's own stated editorial safeguards and its published content; and (c) a semantic sample in which even deliberately-selected "clean" control articles failed independent re-read at a 75% rate (3 of 4), indicating the true problem is likely broader than the 24 structurally-RED / 93 structurally-flagged articles the existing review trail documents. The dominant failure mode — invented, dated, specific personal-history testimony inside a disclosed-fiction framework — is exactly the class of risk the automated citation scanner cannot see, meaning the existing `_reviews` corpus, while extensive (134 files, 694 flagged items), is not an adequate map of where the real risk lives.

---

## 8. REMEDIATION ESTIMATE (approximate — Phase 1 sampled 14% of the corpus; treat as a scoping estimate, not a final count)

- **Immediate action / highest priority:** 1 static page (`research/care-labor.html`) — real-person/real-company factual mismatch on a live public tribunal case. Recommend this be the very first thing looked at once remediation begins, independent of the rest of the corpus.
- **Source repair / research needed:** the 24 structurally-RED articles, plus — given the control-group failure rate — a substantial share of the 107 structurally-AMBER articles almost certainly also need a personal-history-specific re-read the existing citation scanner cannot perform. A defensible planning range is **60–100 of the 142 articles**, pending a Phase 2 semantic pass across the remaining 122 unsampled articles.
- **Light correction (citation-only noise on otherwise-accurate content):** likely the majority of the 93 currently-flagged-but-not-yet-semantically-confirmed articles, once the personal-history layer is separated out from the "real fact, just uncited" layer.
- **No action:** a small minority — 1 of the 20 sampled articles (`camouflaging-is-not-a-skill`) and 3 of the 4 CLEAN controls' *citation* aspects (their personal-history aspects still needed correction) — likely on the order of 10–20 articles corpus-wide, pending verification.
- **Possible archive candidates:** the pre-guardrail Era A articles that rest entirely on an author's claimed personal, undescribed "research" with no dataset ever having existed to recover (e.g. `the-navigation-tax`, `crip-time-is-real-time`) — reconstructing real sourcing for these would likely be disproportionate; correction may mean removing the specific-statistic claims rather than sourcing them.

---

## NEXT DECISION

**LC1 — MATERIAL LEGACY CREDIBILITY RISK; BEGIN PRIORITIZED REMEDIATION.**

Basis: a confirmed real-person/real-company factual mismatch on a live static page, a confirmed contradiction between the site's stated editorial policy and its own published content, and a semantic sample where even control articles failed at a 75% rate — combined with clear evidence that the existing automated review corpus systematically cannot see the dominant failure mode (invented personal-history testimony). The pipeline team is already building the right forward-looking safeguards (Eras E/F); what's missing is applying equivalent scrutiny backward across the 142 already-published articles and the 1 flagged static page.

No public changes made. No deploy. Phase 1 complete — stopping here per instructions.
