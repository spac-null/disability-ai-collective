# V1 seed artifacts — NON-AUTHORITATIVE

Two files from a prior independent research pass, supplied 2026-09-04:

- `CRIP_MINDS_CRAFT_CORPUS_V1.md`
- `cripminds_craft_corpus_v1.json`

## Status

**These are research seeds, not evidence.** Nothing in them is treated as established by V2.
No V1 classification was inherited without checking the source, and no V1 conclusion was
carried into V2 because it already existed.

V2 was completed before these files arrived (commit `17ac705`), from an independently built
corpus. The V1 pass overlapped on 8 of 12 Bregman texts, 0 of 20 Scientias articles, and 4 of
16 craft sources — so the two passes are largely independent samples of the same field, which
is what makes the comparison worth anything.

## How they were used

1. **Avoiding rediscovery.** V1 supplied 22 sources V2 had not seen: 4 Bregman texts, 20
   Scientias articles (all different from V2's 25), and 12 craft-teaching sources.
2. **Bootstrapping ids.** V1's `B##` / `S##` / `C##` ids are carried in the comparison as
   `v1_id` alongside V2's own `BR-` / `SC-` / `CT-` ids. V2's ids remain primary.
3. **Hypotheses worth testing.** V1's transitions claim and its `ARTICLE_FORM` proposal were
   both tested directly and both were revised.
4. **Comparison.** Every V1 source V2 actually used was re-verified and re-coded from the
   original. Results: `../reports/V1_V2_COMPARISON.md` and `v1_v2_adjudication.jsonl`.

## Verification performed

All 48 V1 URLs were fetched. 45 returned HTTP 200; 3 returned 403 (Harvard `C03`, Poynter
`C10`, Poynter `C11`) and are recorded unavailable in V2 rather than accepted on V1's word.
Ten V1 titles differ from the live page title — see the comparison for the assessment.

## Independence guarantee

V2 is defensible with these two files deleted. Every finding in
`../reports/craft_evidence_table_v2.jsonl` cites originals V2 fetched and read, and every
finding added or revised because of a V1 source names that source's URL and quotes the
original rather than V1's paraphrase. The three findings V1 caused V2 to change are marked
`v1_prompted: true` in the evidence table, with the underlying original as the citation.
